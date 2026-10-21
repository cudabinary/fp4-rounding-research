"""Independent NumPy CPU forward; BF16 storage/rounding emulated, no torch/CUDA."""
import pickle,io,zipfile,collections,math
import numpy as np

class Storage:
    def __init__(self,key,count):self.key=key;self.count=count
def rebuild(storage,offset,size,stride,requires_grad,hooks):return (storage,offset,size,stride)
class SafeWeights(pickle.Unpickler):
    def find_class(self,module,name):
        if (module,name)==('collections','OrderedDict'):return collections.OrderedDict
        if (module,name)==('torch','BFloat16Storage'):return 'BF16_STORAGE'
        if (module,name)==('torch._utils','_rebuild_tensor_v2'):return rebuild
        raise ValueError(('Unrecognized pickle global',module,name))
    def persistent_load(self,pid):
        kind,dtype,key,location,count=pid
        assert kind=='storage' and dtype=='BF16_STORAGE' and location=='cpu'
        return Storage(key,count)
def load_weights(path):
    with zipfile.ZipFile(path) as z:
        name=next(n for n in z.namelist() if n.endswith('/data.pkl'));root=name[:-len('data.pkl')]
        spec=SafeWeights(io.BytesIO(z.read(name))).load();state={};cache={}
        for name,(store,offset,size,stride) in spec.items():
            expected=[];step=1
            for length in reversed(size):expected.append(step);step*=length
            assert tuple(reversed(expected))==stride,(name,stride,size)
            if store.key not in cache:
                raw=z.read(root+'data/'+store.key);assert len(raw)==store.count*2
                cache[store.key]=(np.frombuffer(raw,dtype='<u2').astype(np.uint32)<<16).view(np.float32)
            state[name]=cache[store.key][offset:offset+step].reshape(size)
        return state

def bf16(x):
    a=np.asarray(x,dtype=np.float32);u=a.view(np.uint32)
    rounded=(u+np.uint32(0x7fff)+((u>>16)&1))&np.uint32(0xffff0000)
    return rounded.view(np.float32)
def bf_bits(x):return (np.asarray(x,dtype=np.float32).view(np.uint32)>>16).astype('<u2')

class Model:
    def __init__(self,config,state,low_precision=True):
        self.c=config;self.s=state;self.low=low_precision;self.h=config['num_attention_heads'];self.kv=config['num_key_value_heads'];self.d=config['hidden_size']//self.h
        self.freq=(np.float32(1)/(np.float32(config['rope_theta'])**(np.arange(0,self.d,2,dtype=np.float32)/np.float32(self.d)))).astype(np.float32)
    def rnd(self,x):return bf16(x) if self.low else np.asarray(x,dtype=np.float32)
    def norm(self,x,w):
        z=x.astype(np.float32);inv=np.float32(1)/np.sqrt(np.mean(z*z,axis=-1,keepdims=True,dtype=np.float32)+np.float32(self.c['rms_norm_eps']))
        return self.rnd(self.rnd(z*inv)*w)
    def linear(self,x,w):return self.rnd(x@w.T)
    def forward(self,ids,mask=None,past=None,codec=None):
        batch,length=ids.shape;previous=0 if past is None else past[0][0].shape[2]
        pos=np.arange(previous,previous+length,dtype=np.int64);theta=pos.astype(np.float32)[:,None]*self.freq[None,:];emb=np.concatenate((theta,theta),-1)
        cos=self.rnd(np.cos(emb))[None,None];sin=self.rnd(np.sin(emb))[None,None]
        x=self.s['model.embed_tokens.weight'][ids];newpast=[]
        allow=np.arange(previous+length)[None,:]<=pos[:,None];allow=allow[None,None]
        if mask is not None:allow=allow & (mask[:,None,None,:previous+length]!=0)
        def rotate(v):return np.concatenate((-v[...,self.d//2:],v[...,:self.d//2]),-1)
        for layer in range(self.c['num_hidden_layers']):
            p=f'model.layers.{layer}.';res=x;z=self.norm(x,self.s[p+'input_layernorm.weight'])
            q=self.linear(z,self.s[p+'self_attn.q_proj.weight']).reshape(batch,length,self.h,self.d).transpose(0,2,1,3)
            k=self.linear(z,self.s[p+'self_attn.k_proj.weight']).reshape(batch,length,self.kv,self.d).transpose(0,2,1,3)
            v=self.linear(z,self.s[p+'self_attn.v_proj.weight']).reshape(batch,length,self.kv,self.d).transpose(0,2,1,3)
            q=self.rnd(self.rnd(q*cos)+self.rnd(rotate(q)*sin));k=self.rnd(self.rnd(k*cos)+self.rnd(rotate(k)*sin))
            if past is not None:k=np.concatenate((past[layer][0],k),2);v=np.concatenate((past[layer][1],v),2)
            newpast.append((k,v));kk=np.repeat(k,self.h//self.kv,axis=1);vv=np.repeat(v,self.h//self.kv,axis=1)
            scores=(q@kk.swapaxes(-1,-2))/np.float32(math.sqrt(self.d));scores=np.where(allow,scores,np.finfo(np.float32).min)
            scores-=np.max(scores,axis=-1,keepdims=True);prob=np.exp(scores);prob/=prob.sum(axis=-1,keepdims=True,dtype=np.float32)
            # BF16 SDPA is represented by FP32 internal attention then output BF16 rounding.
            a=self.rnd(prob@vv).transpose(0,2,1,3).copy().reshape(batch,length,-1)
            x=self.rnd(res+self.linear(a,self.s[p+'self_attn.o_proj.weight']));res=x;z=self.norm(x,self.s[p+'post_attention_layernorm.weight'])
            gate=self.linear(z,self.s[p+'mlp.gate_proj.weight']);up=self.linear(z,self.s[p+'mlp.up_proj.weight'])
            silu=self.rnd(gate/(np.float32(1)+np.exp(-gate)));a=self.rnd(silu*up);y=self.linear(a,self.s[p+'mlp.down_proj.weight'])
            x=self.rnd(res+y) if codec is None or layer not in [0,15,29] else codec(y,res,layer)
        x=self.norm(x,self.s['model.norm.weight']);return self.linear(x,self.s.get('lm_head.weight',self.s['model.embed_tokens.weight'])),newpast

def nll(logits,targets):
    a=logits.reshape(-1,logits.shape[-1]).astype(np.float64);t=targets.reshape(-1);maximum=np.max(a,axis=1)
    losses=np.log(np.exp(a-maximum[:,None]).sum(axis=1))+maximum-a[np.arange(len(t)),t]
    return float(losses.sum()),losses

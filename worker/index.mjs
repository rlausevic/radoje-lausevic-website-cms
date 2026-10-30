import {contact,contactConfig} from '../server/contact.mjs';
import {metrics} from '../server/metrics.mjs';
export default {async fetch(request,env){
 const path=new URL(request.url).pathname;
 if(path==='/api/metrics')return metrics(request,env);
 if(path==='/api/contact')return contact(request,env);
 if(path==='/api/contact-config')return contactConfig(request,env);
 if(path.startsWith('/api/'))return new Response('Not found',{status:404});
 return env.ASSETS.fetch(request);
}};

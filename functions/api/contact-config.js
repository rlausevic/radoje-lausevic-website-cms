import {contactConfig} from '../../server/contact.mjs';
export const onRequest = ({request,env}) => env.CONTACT_SERVICE
 ? env.CONTACT_SERVICE.fetch(request)
 : contactConfig(request,env);

import {contactConfig} from '../../server/contact.mjs';
export const onRequest = ({request,env}) => contactConfig(request,env);

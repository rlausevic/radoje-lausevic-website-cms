import {contact} from '../../server/contact.mjs';
export const onRequest = ({request,env}) => contact(request,env);

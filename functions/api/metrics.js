import {metrics} from '../../server/metrics.mjs';
// Independent of Contact: bind the dedicated D1 database to this Pages project.
export const onRequest=({request,env})=>metrics(request,env);

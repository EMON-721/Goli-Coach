/** Emit only an API proxy, never an SPA wildcard or a credential-bearing URL. */
export function apiProxy(origin, context='production') {
  if (!origin || context!=='production') return '';
  const url=new URL(origin);
  if(url.protocol!=='https:'||url.username||url.password||url.search||url.hash||url.pathname!=='/')throw Error('BACKEND_ORIGIN must be a bare HTTPS origin');
  return `/api/* ${url.origin}/api/:splat 200!\n`;
}

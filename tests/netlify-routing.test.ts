import {test} from 'node:test';
import assert from 'node:assert/strict';
import {apiProxy} from '../scripts/netlify-routing.mjs';
test('Netlify production proxy keeps API prefix',()=>assert.equal(apiProxy('https://backend.example.test'),'\u002fapi/* https://backend.example.test/api/:splat 200!\n'));
test('Netlify previews cannot reach production accounts',()=>assert.equal(apiProxy('https://backend.example.test','deploy-preview'),''));
test('Device mode has no wildcard API fallback',()=>assert.equal(apiProxy(''),''));
test('Proxy rejects credentials and path injection',()=>{
 for(const value of ['http://backend.example.test','https://user:password@backend.example.test','https://backend.example.test/path','https://backend.example.test/?token=x','https://backend.example.test/#key'])assert.throws(()=>apiProxy(value));
});

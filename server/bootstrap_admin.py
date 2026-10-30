"""Run on the server console to promote an existing account; no default credentials."""
import sys
from app import db,audit
email=input('Existing account email: ').strip().lower()
with db() as c:
 u=c.execute('SELECT id,verified FROM users WHERE email=?',(email,)).fetchone()
 if not u:sys.exit('Register the account first.')
 if not u['verified']:
  if input('Verify this email only after independently confirming ownership? Type CONFIRM: ')!='CONFIRM':sys.exit('Ownership confirmation required.')
  c.execute('UPDATE users SET verified=1 WHERE id=?',(u[0],))
 c.execute("UPDATE users SET role='superadmin' WHERE id=?",(u[0],))
audit('console','superadmin_bootstrap',u[0]);print('Administrator role assigned. Sign in again.')

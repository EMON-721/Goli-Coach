import type {Metadata} from 'next';
import './globals.css';
export const metadata:Metadata={title:'GoliCoach AI · নিজের খেলা, নিজের উন্নতি',description:'A private, Bangla-first cricket practice companion. Review your movement, explore drills and keep a training journal.'};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="bn"><body>{children}</body></html>;}

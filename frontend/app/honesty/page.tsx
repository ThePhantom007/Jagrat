// Redirect legacy /honesty → /app/honesty
import { redirect } from 'next/navigation';
export default function HonestyRedirect() { redirect('/app/honesty'); }

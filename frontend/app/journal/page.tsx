// Redirect legacy /journal → /app/journal
import { redirect } from 'next/navigation';
export default function JournalRedirect() { redirect('/app/journal'); }

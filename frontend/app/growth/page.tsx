// Redirect legacy /growth → /app/growth
import { redirect } from 'next/navigation';
export default function GrowthRedirect() { redirect('/app/growth'); }

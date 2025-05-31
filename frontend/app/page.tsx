import Hero from '../components/hero';
import JournalCreator from '../components/journal-creator';
import Image from 'next/image';

export default function Home() {
  return (
    <main className="min-h-screen relative">
      <div className="fixed inset-0 z-0">
        <Image
          src="/432046b8-76ca-4dfe-a679-c12ef91723b8.png"
          alt="Background"
          fill
          className="object-cover opacity-10"
          priority
        />
        <div className="absolute inset-0 bg-gradient-to-br from-primary/30 via-secondary/30 to-accent/30 mix-blend-multiply"></div>
      </div>
      
      <div className="relative z-10">
        <Hero />
        <JournalCreator />
      </div>
    </main>
  );
}
'use client';

import { useState } from 'react';
import FlightCard from './components/FlightCard';

export default function Home() {
    const [query, setQuery] = useState('');
    const [flights, setFlights] = useState<any[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [hasSearched, setHasSearched] = useState(false);

    const handleSearch = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!query.trim()) return;

        setLoading(true);
        setError('');
        setHasSearched(true);
        setFlights([]);

        try {
            const res = await fetch(`/api/flights?flightNumber=${encodeURIComponent(query)}`);
            if (!res.ok) throw new Error('Failed to fetch flights');
            const data = await res.json();
            setFlights(data);
        } catch (err) {
            setError('An error occurred while fetching flight details.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <main style={{
            maxWidth: '800px',
            margin: '0 auto',
            padding: '40px 20px',
            display: 'flex',
            flexDirection: 'column',
            gap: '40px',
            alignItems: 'center'
        }}>
            <div style={{ textAlign: 'center' }}>
                <h1 style={{
                    fontSize: '3rem',
                    fontWeight: 800,
                    marginBottom: '16px',
                    background: 'linear-gradient(135deg, #fff 0%, #aaa 100%)',
                    WebkitBackgroundClip: 'text',
                    WebkitTextFillColor: 'transparent',
                }}>
                    Flight Tracker
                </h1>
                <p style={{ color: 'hsla(var(--foreground), 0.6)' }}>
                    Real-time flight status and details
                </p>
            </div>

            <form onSubmit={handleSearch} style={{ width: '100%', maxWidth: '500px', position: 'relative' }}>
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter Flight Number (e.g. AA123)"
                    style={{
                        width: '100%',
                        padding: '20px 24px',
                        borderRadius: '50px',
                        border: 'none',
                        background: 'hsla(var(--card-bg), 0.8)',
                        color: 'white',
                        fontSize: '1.1rem',
                        boxShadow: '0 4px 20px rgba(0,0,0,0.2)',
                        outline: 'none',
                        backdropFilter: 'blur(10px)'
                    }}
                />
                <button
                    type="submit"
                    disabled={loading}
                    style={{
                        position: 'absolute',
                        right: '8px',
                        top: '8px',
                        bottom: '8px',
                        padding: '0 32px',
                        borderRadius: '40px',
                        border: 'none',
                        background: 'var(--primary)', // Fallback
                        backgroundColor: 'hsl(var(--primary))',
                        color: 'hsl(var(--background))',
                        fontWeight: 700,
                        cursor: loading ? 'wait' : 'pointer',
                        transition: 'opacity 0.2s',
                        opacity: loading ? 0.7 : 1
                    }}
                >
                    {loading ? '...' : 'Search'}
                </button>
            </form>

            <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {error && (
                    <div style={{
                        padding: '20px',
                        background: 'rgba(255, 68, 68, 0.1)',
                        border: '1px solid rgba(255, 68, 68, 0.2)',
                        borderRadius: '12px',
                        color: '#ff4444',
                        textAlign: 'center'
                    }}>
                        {error}
                    </div>
                )}

                {hasSearched && !loading && flights.length === 0 && !error && (
                    <div style={{ textAlign: 'center', opacity: 0.5 }}>
                        No flights found matching "{query}"
                    </div>
                )}

                {flights.map((flight) => (
                    <FlightCard key={flight.flightNumber} flight={flight} />
                ))}
            </div>
        </main>
    );
}

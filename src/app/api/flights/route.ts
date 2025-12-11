import { NextResponse } from 'next/server';

const MOCK_FLIGHTS = [
    {
        flightNumber: 'AA123',
        airline: 'American Airlines',
        origin: { code: 'JFK', city: 'New York', terminal: '8' },
        destination: { code: 'LHR', city: 'London', terminal: '3' },
        departureTime: '2025-12-08T18:00:00Z',
        arrivalTime: '2025-12-09T06:00:00Z',
        status: 'On Time',
        gate: 'B12'
    },
    {
        flightNumber: 'UA456',
        airline: 'United Airlines',
        origin: { code: 'SFO', city: 'San Francisco', terminal: '3' },
        destination: { code: 'NRT', city: 'Tokyo', terminal: '1' },
        departureTime: '2025-12-08T11:00:00Z',
        arrivalTime: '2025-12-09T15:00:00Z',
        status: 'Delayed',
        gate: 'G4'
    },
    {
        flightNumber: 'DL789',
        airline: 'Delta',
        origin: { code: 'ATL', city: 'Atlanta', terminal: 'S' },
        destination: { code: 'CDG', city: 'Paris', terminal: '2E' },
        departureTime: '2025-12-08T20:30:00Z',
        arrivalTime: '2025-12-09T10:45:00Z',
        status: 'Boarding',
        gate: 'E14'
    }
];

export async function GET(request: Request) {
    const { searchParams } = new URL(request.url);
    const flightNumber = searchParams.get('flightNumber');

    if (!flightNumber) {
        return NextResponse.json({ error: 'Flight number is required' }, { status: 400 });
    }

    // Case insensitive partial match
    const matches = MOCK_FLIGHTS.filter(flight =>
        flight.flightNumber.toLowerCase().includes(flightNumber.toLowerCase())
    );

    await new Promise(resolve => setTimeout(resolve, 800)); // Simulate network delay

    return NextResponse.json(matches);
}

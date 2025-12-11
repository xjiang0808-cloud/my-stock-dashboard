import styles from './FlightCard.module.css';

interface FlightLocation {
    code: string;
    city: string;
    terminal: string;
}

interface Flight {
    flightNumber: string;
    airline: string;
    origin: FlightLocation;
    destination: FlightLocation;
    departureTime: string;
    arrivalTime: string;
    status: string;
    gate: string;
}

const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', timeZoneName: 'short' });
};

const getStatusColor = (status: string) => {
    switch (status) {
        case 'Delayed': return 'var(--destructive, #ff4444)';
        case 'Boarding': return 'var(--warning, #ffbb33)';
        default: return 'var(--success, #00C851)';
    }
};

export default function FlightCard({ flight }: { flight: Flight }) {
    const departureDate = new Date(flight.departureTime);
    const arrivalDate = new Date(flight.arrivalTime);

    // Calculate duration roughly
    const durationMs = arrivalDate.getTime() - departureDate.getTime();
    const hours = Math.floor(durationMs / 3600000);
    const minutes = Math.floor((durationMs % 3600000) / 60000);

    return (
        <div className={styles.card}>
            <div className={styles.header}>
                <span className={styles.airline}>{flight.airline}</span>
                <span className={styles.flightNumber}>{flight.flightNumber}</span>
                <span className={styles.status} style={{ color: getStatusColor(flight.status) }}>
                    {flight.status}
                </span>
            </div>

            <div className={styles.route}>
                <div className={styles.location}>
                    <div className={styles.code}>{flight.origin.code}</div>
                    <div className={styles.city}>{flight.origin.city}</div>
                    <div className={styles.time}>{formatDate(flight.departureTime)}</div>
                    <div className={styles.terminal}>Term {flight.origin.terminal} • Gate {flight.gate}</div>
                </div>

                <div className={styles.path}>
                    <div className={styles.duration}>{hours}h {minutes}m</div>
                    <div className={styles.line}></div>
                    <div className={styles.plane}>✈</div>
                </div>

                <div className={styles.location} style={{ textAlign: 'right' }}>
                    <div className={styles.code}>{flight.destination.code}</div>
                    <div className={styles.city}>{flight.destination.city}</div>
                    <div className={styles.time}>{formatDate(flight.arrivalTime)}</div>
                    <div className={styles.terminal}>Term {flight.destination.terminal}</div>
                </div>
            </div>
        </div>
    );
}

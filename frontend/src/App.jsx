import { useEffect, useState } from "react";
import { apiRequest } from "./api/api";
import "./App.css";

function App() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    const [loggedIn, setLoggedIn] = useState(
        !!localStorage.getItem("access_token")
    );

    const [message, setMessage] = useState("");

    const [drivers, setDrivers] = useState([]);
    const [vehicles, setVehicles] = useState([]);
    const [rides, setRides] = useState([]);

    const [showDrivers, setShowDrivers] = useState(false);
    const [showVehicles, setShowVehicles] = useState(false);
    const [showRides, setShowRides] = useState(false);
    const [showFare, setShowFare] = useState(false);

    const [fareForm, setFareForm] = useState({
        base_fare: "40",
        distance_km: "",
        time_minutes: "",
        surge_multiplier: "1",
    });

    const [fareResult, setFareResult] = useState(null);

    // ============================================================
    // LOAD ALL PAGINATED RESULTS
    // ============================================================

    const loadAllPages = async (endpoint) => {
        let page = 1;
        let allResults = [];

        while (true) {
            const separator = endpoint.includes("?") ? "&" : "?";

            const data = await apiRequest(
                `${endpoint}${separator}page=${page}`
            );

            if (Array.isArray(data)) {
                allResults = [...allResults, ...data];
                break;
            }

            if (data.results) {
                allResults = [...allResults, ...data.results];
            }

            if (!data.next) {
                break;
            }

            page++;
        }

        return allResults;
    };

    // ============================================================
    // LOAD DRIVERS
    // ============================================================

    const loadDrivers = async () => {
        try {
            const data = await loadAllPages("/drivers/");
            setDrivers(data);
        } catch (error) {
            setMessage(error.message);
        }
    };

    // ============================================================
    // LOAD VEHICLES
    // ============================================================

    const loadVehicles = async () => {
        try {
            const data = await loadAllPages("/vehicles/");
            setVehicles(data);
        } catch (error) {
            setMessage(error.message);
        }
    };

    // ============================================================
    // LOAD RIDES
    // ============================================================

    const loadRides = async () => {
        try {
            const data = await loadAllPages("/rides/");
            setRides(data);
        } catch (error) {
            setMessage(error.message);
        }
    };

    // ============================================================
    // INITIAL LOAD
    // ============================================================

    useEffect(() => {
        if (loggedIn) {
            loadDrivers();
            loadVehicles();
            loadRides();
        }
    }, [loggedIn]);

    // ============================================================
    // LOGIN
    // ============================================================

    const handleLogin = async (e) => {
        e.preventDefault();
        setMessage("");

        try {
            const data = await apiRequest("/login/", {
                method: "POST",
                body: JSON.stringify({
                    email,
                    password,
                }),
            });

            localStorage.setItem("access_token", data.access);

            if (data.refresh) {
                localStorage.setItem("refresh_token", data.refresh);
            }

            setLoggedIn(true);
            setMessage("Login successful.");
        } catch (error) {
            setMessage(error.message);
        }
    };

    // ============================================================
    // LOGOUT
    // ============================================================

    const handleLogout = () => {
        localStorage.removeItem("access_token");
        localStorage.removeItem("refresh_token");

        setLoggedIn(false);

        setDrivers([]);
        setVehicles([]);
        setRides([]);

        setFareResult(null);

        setEmail("");
        setPassword("");

        setMessage("Logged out.");
    };

    // ============================================================
    // ACCEPT RIDE
    // ============================================================

    const acceptRide = async (rideId) => {
        try {
            await apiRequest(`/rides/${rideId}/accept/`, {
                method: "POST",
            });

            setMessage("Ride accepted successfully.");

            await loadRides();
        } catch (error) {
            setMessage(error.message);
        }
    };

    // ============================================================
    // CHANGE RIDE STATUS
    // ============================================================

    const changeRideStatus = async (rideId, newStatus) => {
        try {
            await apiRequest(`/rides/${rideId}/status/`, {
                method: "PATCH",
                body: JSON.stringify({
                    status: newStatus,
                }),
            });

            setMessage(`Ride changed to ${newStatus}.`);

            await loadRides();
        } catch (error) {
            setMessage(error.message);
        }
    };

    // ============================================================
    // CANCEL RIDE
    // ============================================================

    const cancelRide = async (rideId) => {
        try {
            await apiRequest(`/rides/${rideId}/cancel/`, {
                method: "POST",
            });

            setMessage("Ride cancelled.");

            await loadRides();
        } catch (error) {
            setMessage(error.message);
        }
    };

    // ============================================================
    // FARE CALCULATION
    // ============================================================

    const calculateFare = async (e) => {
        e.preventDefault();

        setFareResult(null);
        setMessage("");

        try {
            const data = await apiRequest("/fare/calculate/", {
                method: "POST",
                body: JSON.stringify({
                    base_fare: Number(fareForm.base_fare),
                    distance_km: Number(fareForm.distance_km),
                    time_minutes: Number(fareForm.time_minutes),
                    surge_multiplier: Number(
                        fareForm.surge_multiplier
                    ),
                }),
            });

            setFareResult(data.data);

            setMessage("Fare calculated successfully.");
        } catch (error) {
            setMessage(error.message);
        }
    };

    // ============================================================
    // LOGIN PAGE
    // ============================================================

    if (!loggedIn) {
        return (
            <div className="app">

                <div className="login-container">

                    <h1>🚕 Ride Booking</h1>

                    <p>Login to continue</p>

                    <form onSubmit={handleLogin}>

                        <input
                            type="email"
                            placeholder="Email"
                            value={email}
                            onChange={(e) =>
                                setEmail(e.target.value)
                            }
                            required
                        />

                        <input
                            type="password"
                            placeholder="Password"
                            value={password}
                            onChange={(e) =>
                                setPassword(e.target.value)
                            }
                            required
                        />

                        <button type="submit">
                            Login
                        </button>

                    </form>

                    {message && (
                        <p className="message">
                            {message}
                        </p>
                    )}

                </div>

            </div>
        );
    }

    // ============================================================
    // DASHBOARD
    // ============================================================

    return (
        <div className="app">

            <header className="topbar">

                <div>
                    <h1>🚕 Ride Booking</h1>
                    <span>
                        Mobile Backend Dashboard
                    </span>
                </div>

                <button
                    className="logout"
                    onClick={handleLogout}
                >
                    Logout
                </button>

            </header>

            <main className="dashboard">

                {message && (
                    <div className="message">
                        {message}
                    </div>
                )}

                {/* =====================================================
                    DASHBOARD CARDS
                ===================================================== */}

                <div className="dashboard-grid">

                    {/* DRIVERS */}

                    <div
                        className="card clickable"
                        onClick={() => {
                            setShowDrivers(!showDrivers);
                            setShowVehicles(false);
                            setShowRides(false);
                            setShowFare(false);
                        }}
                    >

                        <div className="card-icon">
                            👨‍✈️
                        </div>

                        <h2>Drivers</h2>

                        <p>
                            {drivers.length} drivers
                        </p>

                        <button>
                            View Drivers
                        </button>

                    </div>

                    {/* VEHICLES */}

                    <div
                        className="card clickable"
                        onClick={() => {
                            setShowVehicles(!showVehicles);
                            setShowDrivers(false);
                            setShowRides(false);
                            setShowFare(false);
                        }}
                    >

                        <div className="card-icon">
                            🚗
                        </div>

                        <h2>Vehicles</h2>

                        <p>
                            {vehicles.length} vehicles
                        </p>

                        <button>
                            View Vehicles
                        </button>

                    </div>

                    {/* RIDES */}

                    <div
                        className="card clickable"
                        onClick={() => {
                            setShowRides(!showRides);
                            setShowDrivers(false);
                            setShowVehicles(false);
                            setShowFare(false);
                        }}
                    >

                        <div className="card-icon">
                            📍
                        </div>

                        <h2>Rides</h2>

                        <p>
                            {rides.length} rides
                        </p>

                        <button>
                            View Rides
                        </button>

                    </div>

                    {/* FARE */}

                    <div
                        className="card clickable"
                        onClick={() => {
                            setShowFare(!showFare);
                            setShowDrivers(false);
                            setShowVehicles(false);
                            setShowRides(false);
                        }}
                    >

                        <div className="card-icon">
                            💰
                        </div>

                        <h2>Fare</h2>

                        <p>
                            Calculate ride fare
                        </p>

                        <button>
                            Calculate Fare
                        </button>

                    </div>

                </div>

                {/* =====================================================
                    DRIVERS
                ===================================================== */}

                {showDrivers && (

                    <section className="section">

                        <div className="section-header">

                            <h2>
                                👨‍✈️ Drivers
                            </h2>

                            <button
                                onClick={loadDrivers}
                            >
                                Refresh
                            </button>

                        </div>

                        <div className="items-grid">

                            {drivers.length === 0 ? (

                                <p>
                                    No drivers found.
                                </p>

                            ) : (

                                drivers.map((driver) => (

                                    <div
                                        className="item-card"
                                        key={driver.id}
                                    >

                                        <h3>
                                            {driver.name ||
                                                "Driver"}
                                        </h3>

                                        <p>
                                            <strong>
                                                Email:
                                            </strong>{" "}
                                            {driver.email}
                                        </p>

                                        <p>
                                            <strong>
                                                Phone:
                                            </strong>{" "}
                                            {driver.phone_number ||
                                                "N/A"}
                                        </p>

                                        <p>
                                            <strong>
                                                License:
                                            </strong>{" "}
                                            {driver.license_number}
                                        </p>

                                        <p>
                                            <strong>
                                                Available:
                                            </strong>{" "}
                                            {driver.is_available
                                                ? "Yes"
                                                : "No"}
                                        </p>

                                        <p>
                                            <strong>
                                                Vehicles:
                                            </strong>{" "}
                                            {driver.vehicles
                                                ?.length || 0}
                                        </p>

                                    </div>

                                ))

                            )}

                        </div>

                    </section>

                )}

                {/* =====================================================
                    VEHICLES
                ===================================================== */}

                {showVehicles && (

                    <section className="section">

                        <div className="section-header">

                            <h2>
                                🚗 Vehicles
                            </h2>

                            <button
                                onClick={loadVehicles}
                            >
                                Refresh
                            </button>

                        </div>

                        <div className="items-grid">

                            {vehicles.length === 0 ? (

                                <p>
                                    No vehicles found.
                                </p>

                            ) : (

                                vehicles.map((vehicle) => (

                                    <div
                                        className="item-card"
                                        key={vehicle.id}
                                    >

                                        <h3>
                                            {
                                                vehicle.vehicle_number
                                            }
                                        </h3>

                                        <p>
                                            <strong>
                                                Driver:
                                            </strong>{" "}
                                            {
                                                vehicle.driver_name ||
                                                "N/A"
                                            }
                                        </p>

                                        <p>
                                            <strong>
                                                Type:
                                            </strong>{" "}
                                            {
                                                vehicle.vehicle_type_name ||
                                                "N/A"
                                            }
                                        </p>

                                        <p>
                                            <strong>
                                                Model:
                                            </strong>{" "}
                                            {
                                                vehicle.model_name ||
                                                "N/A"
                                            }
                                        </p>

                                        <p>
                                            <strong>
                                                Color:
                                            </strong>{" "}
                                            {
                                                vehicle.color ||
                                                "N/A"
                                            }
                                        </p>

                                        <p>
                                            <strong>
                                                Active:
                                            </strong>{" "}
                                            {vehicle.is_active
                                                ? "Yes"
                                                : "No"}
                                        </p>

                                    </div>

                                ))

                            )}

                        </div>

                    </section>

                )}

                {/* =====================================================
                    RIDES
                ===================================================== */}

                {showRides && (

                    <section className="section">

                        <div className="section-header">

                            <h2>
                                📍 Rides
                            </h2>

                            <button
                                onClick={loadRides}
                            >
                                Refresh
                            </button>

                        </div>

                        <div className="rides-list">

                            {rides.length === 0 ? (

                                <p>
                                    No rides found.
                                </p>

                            ) : (

                                rides.map((ride) => (

                                    <div
                                        className="ride-card"
                                        key={ride.id}
                                    >

                                        <div className="ride-header">

                                            <h3>
                                                Ride #
                                                {ride.id.slice(
                                                    0,
                                                    8
                                                )}
                                            </h3>

                                            <span
                                                className={`status ${ride.status.toLowerCase()}`}
                                            >
                                                {ride.status}
                                            </span>

                                        </div>

                                        <div className="ride-details">

                                            <p>
                                                <strong>
                                                    Passenger:
                                                </strong>{" "}
                                                {
                                                    ride.passenger_name ||
                                                    "N/A"
                                                }
                                            </p>

                                            <p>
                                                <strong>
                                                    Driver:
                                                </strong>{" "}
                                                {
                                                    ride.driver_name ||
                                                    "Not assigned"
                                                }
                                            </p>

                                            <p>
                                                <strong>
                                                    Vehicle:
                                                </strong>{" "}
                                                {
                                                    ride.vehicle_number ||
                                                    "Not assigned"
                                                }
                                            </p>

                                            <p>
                                                <strong>
                                                    Pickup:
                                                </strong>{" "}
                                                {
                                                    ride.pickup_address ||
                                                    ride.pickup_location ||
                                                    "N/A"
                                                }
                                            </p>

                                            <p>
                                                <strong>
                                                    Drop:
                                                </strong>{" "}
                                                {
                                                    ride.drop_address ||
                                                    ride.drop_location ||
                                                    "N/A"
                                                }
                                            </p>

                                            <p>
                                                <strong>
                                                    Ride Type:
                                                </strong>{" "}
                                                {
                                                    ride.ride_type_name ||
                                                    "N/A"
                                                }
                                            </p>

                                            <p>
                                                <strong>
                                                    Fare:
                                                </strong>{" "}

                                                {ride.fare !== null &&
                                                ride.fare !== undefined
                                                    ? `₹${ride.fare}`
                                                    : "N/A"}

                                            </p>

                                        </div>

                                        {/* =================================================
                                            REQUESTED
                                        ================================================= */}

                                        {ride.status ===
                                            "REQUESTED" && (

                                            <div className="ride-actions">

                                                <button
                                                    onClick={() =>
                                                        acceptRide(
                                                            ride.id
                                                        )
                                                    }
                                                >
                                                    Accept Ride
                                                </button>

                                                <button
                                                    className="danger"
                                                    onClick={() =>
                                                        cancelRide(
                                                            ride.id
                                                        )
                                                    }
                                                >
                                                    Cancel
                                                </button>

                                            </div>

                                        )}

                                        {/* =================================================
                                            ACCEPTED
                                        ================================================= */}

                                        {ride.status ===
                                            "ACCEPTED" && (

                                            <div className="ride-actions">

                                                <button
                                                    onClick={() =>
                                                        changeRideStatus(
                                                            ride.id,
                                                            "DRIVER_ARRIVING"
                                                        )
                                                    }
                                                >
                                                    Driver Arriving
                                                </button>

                                                <button
                                                    className="danger"
                                                    onClick={() =>
                                                        cancelRide(
                                                            ride.id
                                                        )
                                                    }
                                                >
                                                    Cancel
                                                </button>

                                            </div>

                                        )}

                                        {/* =================================================
                                            DRIVER ARRIVING
                                        ================================================= */}

                                        {ride.status ===
                                            "DRIVER_ARRIVING" && (

                                            <div className="ride-actions">

                                                <button
                                                    onClick={() =>
                                                        changeRideStatus(
                                                            ride.id,
                                                            "STARTED"
                                                        )
                                                    }
                                                >
                                                    Start Ride
                                                </button>

                                            </div>

                                        )}

                                        {/* =================================================
                                            STARTED
                                        ================================================= */}

                                        {ride.status ===
                                            "STARTED" && (

                                            <div className="ride-actions">

                                                <button
                                                    onClick={() =>
                                                        changeRideStatus(
                                                            ride.id,
                                                            "COMPLETED"
                                                        )
                                                    }
                                                >
                                                    Complete Ride
                                                </button>

                                            </div>

                                        )}

                                    </div>

                                ))

                            )}

                        </div>

                    </section>

                )}

                {/* =====================================================
                    FARE
                ===================================================== */}

                {showFare && (

                    <section className="section">

                        <div className="section-header">

                            <h2>
                                💰 Fare Calculator
                            </h2>

                        </div>

                        <form
                            className="fare-form"
                            onSubmit={calculateFare}
                        >

                            <label>
                                Base Fare

                                <input
                                    type="number"
                                    step="0.01"
                                    value={
                                        fareForm.base_fare
                                    }
                                    onChange={(e) =>
                                        setFareForm({
                                            ...fareForm,
                                            base_fare:
                                                e.target.value,
                                        })
                                    }
                                    required
                                />

                            </label>

                            <label>
                                Distance (KM)

                                <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    value={
                                        fareForm.distance_km
                                    }
                                    onChange={(e) =>
                                        setFareForm({
                                            ...fareForm,
                                            distance_km:
                                                e.target.value,
                                        })
                                    }
                                    required
                                />

                            </label>

                            <label>
                                Time (Minutes)

                                <input
                                    type="number"
                                    step="0.01"
                                    min="0"
                                    value={
                                        fareForm.time_minutes
                                    }
                                    onChange={(e) =>
                                        setFareForm({
                                            ...fareForm,
                                            time_minutes:
                                                e.target.value,
                                        })
                                    }
                                    required
                                />

                            </label>

                            <label>
                                Surge Multiplier

                                <input
                                    type="number"
                                    step="0.01"
                                    min="1"
                                    value={
                                        fareForm.surge_multiplier
                                    }
                                    onChange={(e) =>
                                        setFareForm({
                                            ...fareForm,
                                            surge_multiplier:
                                                e.target.value,
                                        })
                                    }
                                    required
                                />

                            </label>

                            <button type="submit">
                                Calculate Fare
                            </button>

                        </form>

                        {fareResult && (

                            <div className="fare-result">

                                <h3>
                                    Fare Breakdown
                                </h3>

                                <div>
                                    <span>
                                        Base Fare
                                    </span>

                                    <strong>
                                        ₹
                                        {
                                            fareResult.base_fare
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Distance Fare
                                    </span>

                                    <strong>
                                        ₹
                                        {
                                            fareResult.distance_fare
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Time Fare
                                    </span>

                                    <strong>
                                        ₹
                                        {
                                            fareResult.time_fare
                                        }
                                    </strong>
                                </div>

                                <div>
                                    <span>
                                        Surge
                                    </span>

                                    <strong>
                                        {
                                            fareResult.surge
                                        }
                                    </strong>
                                </div>

                                <hr />

                                <div className="total">

                                    <span>
                                        Total Fare
                                    </span>

                                    <strong>
                                        ₹
                                        {
                                            fareResult.total
                                        }
                                    </strong>

                                </div>

                            </div>

                        )}

                    </section>

                )}

            </main>

        </div>
    );
}

export default App;
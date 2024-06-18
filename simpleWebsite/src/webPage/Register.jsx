import React, {useContext, useState} from 'react';
import axios from 'axios';
import Navbar from '../components/Navbar';
import {Link, useNavigate} from "react-router-dom";
import {AuthContext} from "../components/AuthContext";

function Register() {
    const {setIsLoggedIn} = useContext(AuthContext);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleRegister = async (e) => {
        e.preventDefault();
        axios.post('http://localhost:5000/register', {
                username,
                password
            }, {withCredentials: true}
        ).then(response => {
                if (response.data.error) {
                    setError(response.data.error);
                    return;
                }
                axios.post('http://localhost:5000/login', {
                        username,
                        password
                    }, {withCredentials: true}
                ).then(response => {
                        if (response.data.error) {
                            setError(response.data.error);
                            return;
                        }
                        setIsLoggedIn(true);
                        navigate('/');
                    }
                ).catch(error => {
                        setError('An error occurred during login.');
                    }
                );
            }
        ).catch(error => {
                setError('An error occurred during registration.');
            }
        );
    };

    return (
        <div className="background_container1">
            <Navbar/>
            <div className="wrapper list-container">
                <form onSubmit={handleRegister}>
                    <h1>Register</h1>
                    <div className="input-box">
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            placeholder="Username"
                            required
                        />
                        <i className="bx bxs-user"></i>
                    </div>
                    <div className="input-box">
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Password"
                        />
                        <i className="bx bxs-user"></i>
                    </div>
                    <button type="submit" className="btn-submit">Sign up</button>
                    <div className="register-link">
                        <p>You have a account?<Link to="/login"> Sing in</Link></p>
                    </div>
                    {error && <p className="error">{error}</p>}
                </form>
            </div>
        </div>
    );
}

export default Register;

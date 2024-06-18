import React, { useContext, useState } from 'react';
import axios from 'axios';
import Navbar from '../components/Navbar';
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../components/AuthContext";

function Register() {
    const { setIsLoggedIn } = useContext(AuthContext);
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const handleRegister = async (e) => {
        e.preventDefault();
        axios.post('http://localhost:5000/register', {
            username,
            password
        }, { withCredentials: true }
        ).then(response => {
            axios.post('http://localhost:5000/login', {
                username,
                password
            }, { withCredentials: true }
            ).then(response => {
                //需要創建註冊與正在登入畫面
                setIsLoggedIn(true);
                navigate('/');
            }).catch(error => {
                if(error.response && error.response.status === 401)
                    setError('Invalid username or password.');
                else if (error.response&& error.response.status === 500)
                    setError('An error occurred during login.');
                else
                    setError('Network error. Please try again later.');
            });
        }).catch(error => {
            if (error.response && error.response.status === 409)
                setError('Username already exists.');
            else if (error.response && error.response.status === 500)
                setError('An error occurred during login.');
            else
                setError('Network error. Please try again later.');
        });
    };

    return (
        <div className="background_container1">
            <Navbar />
            <div className="wrapper list-container">
                <form onSubmit={handleRegister}>
                    <h1>Sign Up</h1>
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
                    {error && <div className="error">{error}</div>}
                </form>
            </div>
        </div>
    );
}

export default Register;

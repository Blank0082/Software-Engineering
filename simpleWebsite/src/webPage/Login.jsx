import React, { useContext, useState } from 'react';
import axios from 'axios';
import Navbar from "../components/Navbar";
import '../css/LoginRegister.css';
import { Link, useNavigate } from "react-router-dom";
import { AuthContext } from "../components/AuthContext";

function Login() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const { setIsLoggedIn } = useContext(AuthContext);
    const navigate = useNavigate();

    const handleLogin = async (e) => {
        e.preventDefault();
        axios.post('http://localhost:5000/login', {
            username,
            password
        }, { withCredentials: true }
        ).then(response => {
            //需要創建登入成功畫面
            setIsLoggedIn(true);
            navigate('/');
        }
        ).catch(error => {
            if (error.response && error.response.status === 401)
                setError('Invalid username or password.');
            else if (error.response && error.response.status === 500)
                setError('An error occurred during login.');
            else
                setError('Network error. Please try again later.');
        }
        );
    };

    return (
        <div className="background_container1">
            <Navbar />
            <div className="wrapper list-container">
                <form onSubmit={handleLogin}>
                    <h1>Welcome</h1>
                    <div className="input-box">
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => {
                                setUsername(e.target.value);
                                setError('');
                            }}
                            placeholder="Username"
                            required
                        />
                        <i className="bx bxs-user"></i>
                    </div>
                    <div className="input-box">
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => {
                                setPassword(e.target.value)
                                setError('');
                            }
                            }
                            placeholder="Password"
                            required
                        />
                        <i className="bx bxs-lock-alt"></i>
                    </div>
                    <button type="submit" className="btn-submit">Sign in</button>
                    <div className="register-link">
                        <p>Don't have a account?<Link to="/register"> Sign up</Link></p>
                    </div>
                    {error && <div className="error">{error}</div>}
                </form>
            </div>
        </div>
    );
}

export default Login;

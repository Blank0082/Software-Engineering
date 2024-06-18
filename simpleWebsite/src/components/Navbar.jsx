import {Link, useNavigate} from 'react-router-dom';
import '../css/Navbar.css';
import logo from "../img/logo.jpg";
import React, {useContext, useEffect, useState} from "react";
import axios from "axios";
import {AuthContext} from "./AuthContext";

export default function Navbar() {
    const {isLoggedIn,setIsLoggedIn} = useContext(AuthContext);
    const [showDropdown, setShowDropdown] = useState(false);
    const [darkMode, setDarkMode] = useState(() => {
        const savedMode = localStorage.getItem('darkMode');
        return savedMode ? JSON.parse(savedMode) : false;
    });
    const navigate = useNavigate();

    useEffect(() => {
        document.body.className = darkMode ? 'dark-mode' : 'light-mode';
        localStorage.setItem('darkMode', JSON.stringify(darkMode));
    }, [darkMode]);

    const toggleDarkMode = () => {
        setDarkMode(!darkMode);
    };
    const handleLogout = async () => {
        await axios.post('http://localhost:5000/logout', {}, {withCredentials: true});
        setIsLoggedIn(false);
        navigate("/");
    };
    const toggleDropdown = () => {
        setShowDropdown(!showDropdown);
    };


    return (
        <nav>
            <div className="navbar-container">
                <Link to="/">
                    <img alt="Logo" className="logo-img" src={logo}></img>
                </Link>
                <div className="btn-group">
                    <Link to="/" className="link-style">首頁</Link>
                    {isLoggedIn ? (
                        <>
                            <Link to="/upload" className="link-style">上傳圖片</Link>
                            <div className="user-menu">
                                <button className="btn" onClick={toggleDropdown}>
                                    <i className="bx bxs-user"/>帳號
                                </button>
                                {showDropdown && (
                                    <div className="dropdown-menu">
                                        <Link to="/history" className="dropdown-item">辨識記錄</Link>
                                        <Link to="/" className="dropdown-item" onClick={handleLogout}>登出</Link>
                                    </div>
                                )}
                            </div>
                        </>
                    ) : (
                        <>
                            <Link to="/login" className="link-style">登入</Link>
                            <Link to="/register" className="link-style">註冊</Link>
                        </>
                    )}
                    <label className="switch">
                        <input type="checkbox" checked={darkMode} onChange={toggleDarkMode}/>
                        <span className="slider"></span>
                    </label>
                </div>
            </div>
        </nav>
    );
}
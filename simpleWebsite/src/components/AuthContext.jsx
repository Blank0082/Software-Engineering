import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [authChecked, setAuthChecked] = useState(false);

    useEffect(() => {
        const checkAuth = async () => {
            axios.get('http://localhost:5000/checkAuth', { withCredentials: true })
                .then(response => {
                    console.log('Login success.');
                    setIsLoggedIn(true);
                }).catch(error => {
                    if (error.response) {
                        console.log(error.response.data.error);
                    } else {
                        console.log(error+"\nserver error");
                    }
                    setIsLoggedIn(false);
                }).finally(() => {
                    setAuthChecked(true);
                });
        }
        checkAuth();
    }, []);

    return (
        <AuthContext.Provider value={{ isLoggedIn, setIsLoggedIn, authChecked }}>
            {children}
        </AuthContext.Provider>
    );
};
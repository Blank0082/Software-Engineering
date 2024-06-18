import React, { createContext, useState, useEffect } from 'react';
import axios from 'axios';

export const AuthContext = createContext();

export const AuthProvider = ({ children }) => {
    const [isLoggedIn, setIsLoggedIn] = useState(false);
    const [authChecked, setAuthChecked] = useState(false);

    useEffect(() => {
        const checkAuth = async () => {
            try {
                const response = await axios.get('http://localhost:5000/checkAuth', { withCredentials: true });
                if (response.data.status === 'ok') {
                    console.log(response.data);
                    setIsLoggedIn(true);
                } else {
                    console.log(response.data);
                    setIsLoggedIn(false);
                }
            } catch (error) {
                if(error.response!==undefined){
                    console.log(error.response.data);
                }else{
                    console.log(error);
                }
                setIsLoggedIn(false);
            } finally {
                setAuthChecked(true);
            }
        };

        checkAuth();
    }, []);

    return (
        <AuthContext.Provider value={{ isLoggedIn, setIsLoggedIn, authChecked }}>
            {children}
        </AuthContext.Provider>
    );
};
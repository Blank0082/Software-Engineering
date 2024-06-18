import React from 'react';
import {Routes, Route} from "react-router-dom";
import Login from './webPage/Login';
import Register from './webPage/Register';
import ErrorPage from "./error/errorPage";
import Logout from './webPage/Logout';
import Home from './webPage/Home';
import Upload from './webPage/Upload';
import Result from './webPage/Result';
import History from "./webPage/History";
import './App.css';
import 'boxicons/css/boxicons.min.css';

function App() {
    return (
        <Routes>
            <Route path='/' element={<Home/>}/>
            <Route path="/login" element={<Login/>}/>
            <Route path="/register" element={<Register/>}/>
            <Route path="/logout" element={<Logout/>}/>
            <Route path="/upload" element={<Upload/>}/>
            <Route path="/result" element={<Result/>}/>
            <Route path="/history" element={<History/>}/>
            <Route path='*' element={<ErrorPage/>}/>
        </Routes>
    );
}

export default App;

import React from 'react';
import "../css/error.css";
import Navbar from "../components/Navbar";

export default function ErrorPage() {
    return (
        <div className="background_container1">
            <Navbar/>
            <p className="p-404">Not Found
                <br/>
                <span className="bigger flickering">404</span>
                <br/>we can't find this page.
            </p>
        </div>
    )
}

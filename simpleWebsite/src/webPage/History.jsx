import React, { useContext, useEffect, useState } from 'react';
import { useNavigate } from "react-router-dom";
import axios from 'axios';
import Navbar from '../components/Navbar';
import '../css/history.css';
import { AuthContext } from "../components/AuthContext";

export default function History() {
    const [files, setFiles] = useState([]);
    const navigate = useNavigate();
    const { isLoggedIn, authChecked } = useContext(AuthContext);

    useEffect(() => {
        if (authChecked && !isLoggedIn) {
            navigate("/login");
        }
    }, [isLoggedIn, authChecked, navigate]);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const response = await axios.get('http://localhost:5000/history', { withCredentials: true });
                if (response.data.status === 'ok') {
                    setFiles(response.data.files);
                } else {
                    console.log(response.data);
                }
            } catch (error) {
                console.log(error.response.data);
            }
        };
        fetchHistory();
    }, []);

    return (
        <div className="history-page">
            <Navbar />
            <div className="history-container">
                <h2>Upload History</h2>
                {files.length === 0 ? (
                    <p>No uploads found.</p>
                ) : (
                    <ul className="file-list">
                        {files.map((file) => (
                            <li key={file._id} className="file-item">
                                <div className="file-info">
                                    <p><strong>Filename:</strong> {file.originalFilename}</p>
                                    <p><strong>Result:</strong> {file.result}</p>
                                </div>
                                <div className="file-preview">
                                    <img src={`http://localhost:5000/uploads/${file.filename}`} alt={file.filename}
                                        className="preview-image" />
                                </div>
                            </li>
                        ))}
                    </ul>
                )}
            </div>
        </div>
    );
}

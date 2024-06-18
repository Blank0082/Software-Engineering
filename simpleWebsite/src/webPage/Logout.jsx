import {useNavigate} from 'react-router-dom';
import {useEffect} from "react";

function Logout() {
    const history = useNavigate();

    useEffect(() => {
        localStorage.removeItem('token');
        history.push('/login');
    }, [history]);

    return null;
}

export default Logout;

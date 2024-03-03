import React from 'react';
import styles from './style.module.css'; // Ensure the path is correct

export const Loader = ({ onSuccess }) => {
    return (
        <div className={styles.overlay}>
            <div className={styles.loader}></div>
        </div>   
      );
    
};    
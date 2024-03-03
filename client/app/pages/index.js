// pages/index.js or pages/home.js
import Head from 'next/head';
import { useState } from 'react';
import { FileUploader } from '../components/FileUploader';
import { ToastContainer } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';
import styles from '../styles/Home.module.css';

export default function Home() {
  const [files, setFiles] = useState([]);

  const onSuccess = (savedFiles) => {
    setFiles(savedFiles);
  };

  return (
    <div className={styles.container}>
      <Head>
        <title>Upload and Generate</title>
      </Head>
      <FileUploader onSuccess={onSuccess} />
      <ToastContainer />
    </div>
  );
}

import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from 'styled-components';
import { CssBaseline } from '@mui/material';
import { theme } from './styles/theme';
import { GlobalStyles } from './styles/globalStyles';
import Navbar from './components/Navbar';
import FaceRegister from './components/FaceRegister';
import FaceSearch from './components/FaceSearch';
import FaceStats from './components/FaceStats';

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <GlobalStyles />
      <Router>
        <Navbar />
        <Routes>
          <Route path="/" element={<FaceRegister />} />
          <Route path="/register" element={<FaceRegister />} />
          <Route path="/search" element={<FaceSearch />} />
          <Route path="/stats" element={<FaceStats />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;
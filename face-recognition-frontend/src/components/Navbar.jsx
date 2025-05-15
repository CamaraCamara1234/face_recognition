import React from 'react';
import { AppBar, Toolbar, Typography, Button, Container, Box, Avatar } from '@mui/material';
import { Link } from 'react-router-dom';

const Navbar = () => {
  return (
    <AppBar position="static" sx={{ backgroundColor: '#1a237e' }}>
      <Container maxWidth="xl">
        <Toolbar disableGutters>
          {/* Logo + Titre */}
          <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
            <Avatar 
              alt="Logo" 
              src="/xayone.png" 
              sx={{ 
                width: 120, 
                height: 50,
                mr: 1,
                backgroundColor: 'white',
                padding: 0.5,
                borderRadius: 1.5,
                boxShadow: '0 2px 8px rgba(0,0,0,0.15)'
              }} 
              variant="square"
            />
            <Typography 
              variant="h6" 
              noWrap 
              component={Link} 
              to="/"
              sx={{
                fontFamily: 'monospace',
                fontWeight: 700,
                letterSpacing: '.2rem',
                color: 'inherit',
                textDecoration: 'none',
              }}
            >
              FACE ID
            </Typography>
          </Box>

          {/* Espace flexible */}
          <Box sx={{ flexGrow: 1 }} />

          {/* Boutons de navigation */}
          <Box sx={{ display: { xs: 'none', md: 'flex' } }}>
            <Button 
              color="inherit" 
              component={Link} 
              to="/register"
              sx={{ mx: 1 }}
            >
              Register
            </Button>
            <Button 
              color="inherit" 
              component={Link} 
              to="/search"
              sx={{ mx: 1 }}
            >
              Search
            </Button>
            <Button 
              color="inherit" 
              component={Link} 
              to="/stats"
              sx={{ mx: 1 }}
            >
              Stats
            </Button>

            <Button 
              color="inherit" 
              component={Link} 
              to="/database"
              sx={{ mx: 1 }}
            >
              Database
            </Button>
          </Box>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Navbar;
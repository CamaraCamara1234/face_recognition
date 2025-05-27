import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Typography, 
  Card, 
  CardContent, 
  CircularProgress,
  Alert,
  Button,
  Paper,
  Grid,
  Divider
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import axios from 'axios';

const FaceStats = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetchStats = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await axios.get('http://localhost:8000/statitistique/');
      setStats(response.data);
    } catch (err) {
      setError(err.response?.data?.error || err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const formatIndexType = (type) => {
    if (!type) return 'Inconnu';
    return type.replace('Index', '').replace('faiss.', '');
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 4 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h5" component="h2">
          Statistiques de la Base Faciale
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={fetchStats}
          disabled={loading}
        >
          Actualiser
        </Button>
      </Box>

      {loading && (
        <Box display="flex" justifyContent="center" my={4}>
          <CircularProgress />
        </Box>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Erreur lors du chargement: {error}
        </Alert>
      )}

      {stats && stats.success && (
        <Card variant="outlined">
          <CardContent>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <StatItem 
                  label="Nombre de visages enregistrés" 
                  value={stats.count} 
                  icon="👤"
                />
                <Divider sx={{ my: 2 }} />
                <StatItem 
                  label="Dimension des embeddings" 
                  value={`${stats.dimension}D`} 
                  icon="📏"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <StatItem 
                  label="Type d'index FAISS" 
                  value={formatIndexType(stats.index_type)} 
                  icon="🔍"
                />
                <Divider sx={{ my: 2 }} />
                <StatItem 
                  label="Dernière mise à jour" 
                  value={stats.last_update || 'Non disponible'} 
                  icon="🕒"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {stats && !stats.success && (
        <Alert severity="warning">
          Impossible de récupérer les statistiques: {stats.message}
        </Alert>
      )}
    </Paper>
  );
};

const StatItem = ({ label, value, icon }) => (
  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
    <Typography variant="h4" component="span">
      {icon}
    </Typography>
    <Box>
      <Typography variant="subtitle2" color="text.secondary">
        {label}
      </Typography>
      <Typography variant="h6" component="div">
        {value}
      </Typography>
    </Box>
  </Box>
);

export default FaceStats;
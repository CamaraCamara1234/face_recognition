import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  TextField,
  Typography,
  Paper,
  Alert,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogTitle,
  DialogContent,
  DialogContentText,
  List,
  ListItem,
  ListItemText,
  Divider
} from '@mui/material';
import axios from 'axios';

const UserManagement = () => {
  // États initiaux
  const [userId, setUserId] = useState('');
  const [loading, setLoading] = useState({
    delete: false,
    clear: false,
    refresh: false
  });
  const [message, setMessage] = useState(null);
  const [openDialog, setOpenDialog] = useState(false);
  const [users, setUsers] = useState([]);
  const [stats, setStats] = useState({ count: 0, last_update: null });

  // Chargement initial des données
  useEffect(() => {
    fetchDatabaseStats();
  }, []);

  // Récupère les statistiques et la liste des utilisateurs
  const fetchDatabaseStats = async () => {
    setLoading(prev => ({ ...prev, refresh: true }));
    setMessage(null);
    
    try {
      const [statsResponse, usersResponse] = await Promise.all([
        axios.get('http://localhost:8000/stats'),
        axios.get('http://localhost:8000/list_users').catch(() => ({ data: { users: [] }}))
      ]);

      setStats(statsResponse.data);
      setUsers(usersResponse.data.users || []);
    } catch (error) {
      setMessage({
        text: 'Erreur lors du chargement des données',
        severity: 'error',
        details: error.response?.data?.error || error.message
      });
    } finally {
      setLoading(prev => ({ ...prev, refresh: false }));
    }
  };

  // Supprime un utilisateur spécifique
  const handleDelete = async () => {
    if (!userId.trim()) {
      setMessage({ text: 'Veuillez entrer un ID utilisateur valide', severity: 'error' });
      return;
    }

    setLoading(prev => ({ ...prev, delete: true }));
    setMessage(null);

    try {
      // 1. Suppression
      // eslint-disable-next-line no-unused-vars
      const deleteResponse = await axios.delete(
        `http://localhost:8000/delete_user?user_id=${encodeURIComponent(userId.trim())}`
      );

      // 2. Vérification après un court délai
      await new Promise(resolve => setTimeout(resolve, 300));
      await fetchDatabaseStats();

      // 3. Feedback
      setMessage({
        text: `Utilisateur ${userId} supprimé avec succès`,
        severity: 'success'
      });
      setUserId('');
    } catch (error) {
      setMessage({
        text: error.response?.data?.message || 'Échec de la suppression',
        severity: 'error',
        details: error.response?.data?.error || error.message
      });
    } finally {
      setLoading(prev => ({ ...prev, delete: false }));
    }
  };

  // Vide toute la base de données
  const handleClearDatabase = async () => {
    setLoading(prev => ({ ...prev, clear: true }));
    setMessage(null);

    try {
      await axios.post('http://localhost:8000/clear_database/');
      await fetchDatabaseStats();
      setMessage({
        text: 'Base de données vidée avec succès',
        severity: 'success'
      });
    } catch (error) {
      setMessage({
        text: 'Échec de la suppression complète',
        severity: 'error',
        details: error.response?.data?.error || error.message
      });
    } finally {
      setLoading(prev => ({ ...prev, clear: false }));
      setOpenDialog(false);
    }
  };

  return (
    <Paper elevation={3} sx={{ p: 3, mt: 2, mb: 4 }}>
      <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
        Gestion des Utilisateurs
      </Typography>

      {/* Statistiques */}
      <Box sx={{ 
        mb: 3, 
        p: 2, 
        bgcolor: 'background.default', 
        borderRadius: 1,
        border: '1px solid',
        borderColor: 'divider'
      }}>
        <Typography variant="subtitle2" sx={{ fontWeight: 500 }}>
          Statut actuel: {stats?.count || 0} utilisateur(s) enregistré(s)
        </Typography>
        {stats?.last_update && (
          <Typography variant="caption" display="block" sx={{ mt: 0.5 }}>
            Dernière mise à jour: {new Date(stats.last_update).toLocaleString()}
          </Typography>
        )}
      </Box>

      {/* Liste des utilisateurs */}
      {Array.isArray(users) && users.length > 0 ? (
        <Box sx={{ 
          mb: 3, 
          maxHeight: 250, 
          overflow: 'auto',
          border: '1px solid',
          borderColor: 'divider',
          borderRadius: 1
        }}>
          <List dense>
            {users.map((user, index) => (
              <React.Fragment key={user?.id || index}>
                <ListItem>
                  <ListItemText
                    primary={user?.id || 'ID inconnu'}
                    secondary={user?.timestamp ? 
                      `Enregistré le: ${new Date(user.timestamp).toLocaleString()}` : 
                      'Date inconnue'}
                  />
                </ListItem>
                {index < users.length - 1 && <Divider component="li" />}
              </React.Fragment>
            ))}
          </List>
        </Box>
      ) : (
        <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
          Aucun utilisateur enregistré dans la base de données
        </Typography>
      )}

      {/* Messages d'alerte */}
      {message && (
        <Alert 
          severity={message.severity} 
          sx={{ mb: 2 }}
          onClose={() => setMessage(null)}
        >
          <Box>
            <Typography>{message.text}</Typography>
            {message.details && (
              <Typography variant="caption" component="div" sx={{ mt: 0.5 }}>
                Détails: {message.details}
              </Typography>
            )}
          </Box>
        </Alert>
      )}

      {/* Formulaire de suppression */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ mb: 1 }}>
          Supprimer un utilisateur spécifique
        </Typography>
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <TextField
            label="ID Utilisateur"
            variant="outlined"
            fullWidth
            size="small"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            disabled={loading.delete || loading.clear}
          />
          <Button
            variant="contained"
            color="error"
            onClick={handleDelete}
            disabled={loading.delete || loading.clear || !userId.trim()}
            sx={{ 
              minWidth: 120,
              height: '40px' // Aligne avec le TextField
            }}
          >
            {loading.delete ? (
              <CircularProgress size={20} color="inherit" />
            ) : (
              'Supprimer'
            )}
          </Button>
        </Box>
      </Box>

      {/* Bouton d'actualisation */}
      <Box sx={{ mb: 3 }}>
        <Button
          variant="outlined"
          onClick={fetchDatabaseStats}
          disabled={loading.refresh}
          fullWidth
        >
          {loading.refresh ? (
            <CircularProgress size={20} />
          ) : (
            'Actualiser les Données'
          )}
        </Button>
      </Box>

      {/* Bouton de suppression globale */}
      <Box sx={{ mb: 2 }}>
        <Typography variant="subtitle2" gutterBottom sx={{ mb: 1 }}>
          Actions Administratives
        </Typography>
        <Button
          variant="contained"
          color="error"
          onClick={() => setOpenDialog(true)}
          disabled={loading.delete || loading.clear || loading.refresh || stats?.count === 0}
          fullWidth
          sx={{ py: 1 }}
        >
          {loading.clear ? (
            <CircularProgress size={20} color="inherit" />
          ) : (
            'Vider Toute la Base de Données'
          )}
        </Button>
      </Box>

      {/* Dialogue de confirmation */}
      <Dialog 
        open={openDialog} 
        onClose={() => !loading.clear && setOpenDialog(false)}
      >
        <DialogTitle>
          Confirmer la suppression complète
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Vous êtes sur le point de supprimer définitivement {stats?.count || 0} enregistrement(s).
            <br />
            <strong>Cette action est irréversible.</strong>
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setOpenDialog(false)} 
            disabled={loading.clear}
            color="inherit"
          >
            Annuler
          </Button>
          <Button 
            onClick={handleClearDatabase} 
            color="error"
            disabled={loading.clear}
            startIcon={loading.clear ? <CircularProgress size={20} color="inherit" /> : null}
          >
            Confirmer
          </Button>
        </DialogActions>
      </Dialog>
    </Paper>
  );
};

export default UserManagement;
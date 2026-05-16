import { useContext } from 'react';
import { AuthContext } from '../context/AuthContext';

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const useHasRole = (roles) => {
  const { user } = useAuth();
  if (!user || !user.roles) return false;
  if (typeof roles === 'string') {
    return user.roles.includes(roles);
  }
  return roles.some((role) => user.roles.includes(role));
};

export const useHasPermission = (permission) => {
  const { user } = useAuth();
  if (!user || !user.permissions) return false;
  return user.permissions.includes(permission);
};

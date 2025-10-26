import React, { useEffect } from 'react';
import { useDispatch } from 'react-redux';
import { onAuthStateChanged } from 'firebase/auth';
import { auth } from '../utils/firebase';
import { login } from '../features/auth/authSlice';

export const AuthWrapper = ({ children }) => {
  const dispatch = useDispatch();

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (user) => {
      if (user) {
        // User is signed in
        const userEmail = user.email || '';
        const defaultName = userEmail && userEmail.includes('@') ? userEmail.split('@')[0] : 'User';

        dispatch(
          login({
            uid: user.uid,
            email: user.email,
            name: user.displayName || defaultName,
          })
        );
      } else {
        // User is signed out
        // Handle logout if needed
      }
    });

    return () => unsubscribe();
  }, [dispatch]);

  return <>{children}</>;
};

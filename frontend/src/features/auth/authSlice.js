import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import {
  signInWithEmailAndPassword,
  signOut,
  createUserWithEmailAndPassword,
  sendPasswordResetEmail,
} from 'firebase/auth';
import { auth } from '../../utils/firebase';

export const login = createAsyncThunk(
  'auth/login',
  async ({ email, password }, { rejectWithValue }) => {
    try {
      const userCredential = await signInWithEmailAndPassword(auth, email, password);
      const userEmail = userCredential.user.email || '';
      const defaultName = userEmail && userEmail.includes('@') ? userEmail.split('@')[0] : 'User';

      return {
        uid: userCredential.user.uid,
        email: userCredential.user.email,
        name: userCredential.user.displayName || defaultName,
      };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const register = createAsyncThunk(
  'auth/register',
  async ({ name, email, password }, { rejectWithValue }) => {
    try {
      const userCredential = await createUserWithEmailAndPassword(auth, email, password);
      const userEmail = userCredential.user.email || email || '';
      const defaultName = userEmail && userEmail.includes('@') ? userEmail.split('@')[0] : 'User';

      // In a real app, you would also save the user data to Firestore
      return {
        uid: userCredential.user.uid,
        email: userCredential.user.email,
        name: name || defaultName,
      };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

export const logout = createAsyncThunk('auth/logout', async (_, { rejectWithValue }) => {
  try {
    await signOut(auth);
    return true;
  } catch (error) {
    return rejectWithValue(error.message);
  }
});

export const resetPassword = createAsyncThunk(
  'auth/resetPassword',
  async (email, { rejectWithValue }) => {
    try {
      await sendPasswordResetEmail(auth, email);
      return { success: true, email };
    } catch (error) {
      return rejectWithValue(error.message);
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState: {
    user: null,
    status: 'idle',
    error: null,
    resetPasswordStatus: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      // Login
      .addCase(login.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.user = action.payload;
      })
      .addCase(login.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      // Register
      .addCase(register.pending, (state) => {
        state.status = 'loading';
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.user = action.payload;
      })
      .addCase(register.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.payload;
      })
      // Logout
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.status = 'idle';
      })
      // Reset Password
      .addCase(resetPassword.pending, (state) => {
        state.resetPasswordStatus = 'loading';
      })
      .addCase(resetPassword.fulfilled, (state, action) => {
        state.resetPasswordStatus = { success: true, email: action.payload.email };
      })
      .addCase(resetPassword.rejected, (state, action) => {
        state.resetPasswordStatus = { success: false, error: action.payload };
      });
  },
});

export default authSlice.reducer;

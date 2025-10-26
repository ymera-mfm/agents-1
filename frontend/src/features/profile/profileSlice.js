import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { doc, getDoc, updateDoc } from 'firebase/firestore';
import { db } from '../../utils/firebase';
import { updateEmail, updatePassword, updateProfile } from 'firebase/auth';
import { auth } from '../../utils/firebase';

export const fetchProfile = createAsyncThunk('profile/fetchProfile', async (userId) => {
  const docRef = doc(db, 'users', userId);
  const docSnap = await getDoc(docRef);
  return docSnap.exists() ? docSnap.data() : null;
});

export const updateProfileData = createAsyncThunk(
  'profile/updateProfile',
  async ({ userId, updates }) => {
    const userDocRef = doc(db, 'users', userId);
    await updateDoc(userDocRef, updates);

    // Update Firebase Auth profile if email or name changes
    if (updates.email) {
      await updateEmail(auth.currentUser, updates.email);
    }
    if (updates.name) {
      await updateProfile(auth.currentUser, { displayName: updates.name });
    }

    return updates;
  }
);

export const changePassword = createAsyncThunk(
  'profile/changePassword',
  async ({ currentPassword: _currentPassword, newPassword }) => {
    // In a real app, you would reauthenticate the user first
    await updatePassword(auth.currentUser, newPassword);
    return { success: true };
  }
);

const profileSlice = createSlice({
  name: 'profile',
  initialState: {
    data: null,
    status: 'idle',
    error: null,
  },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchProfile.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchProfile.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.data = action.payload;
      })
      .addCase(fetchProfile.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      .addCase(updateProfileData.fulfilled, (state, action) => {
        state.data = { ...state.data, ...action.payload };
      });
  },
});

export default profileSlice.reducer;

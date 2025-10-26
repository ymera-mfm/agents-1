import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { collection, getDocs, addDoc, updateDoc, doc } from 'firebase/firestore';
import { db } from '../../utils/firebase';

export const fetchProjects = createAsyncThunk('projects/fetchProjects', async () => {
  const querySnapshot = await getDocs(collection(db, 'projects'));
  return querySnapshot.docs.map((doc) => ({ id: doc.id, ...doc.data() }));
});

export const addProject = createAsyncThunk('projects/addProject', async (project) => {
  const docRef = await addDoc(collection(db, 'projects'), project);
  return { id: docRef.id, ...project };
});

export const updateProject = createAsyncThunk('projects/updateProject', async ({ id, updates }) => {
  await updateDoc(doc(db, 'projects', id), updates);
  return { id, updates };
});

const projectsSlice = createSlice({
  name: 'projects',
  initialState: { data: [], status: 'idle', error: null },
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchProjects.pending, (state) => {
        state.status = 'loading';
      })
      .addCase(fetchProjects.fulfilled, (state, action) => {
        state.status = 'succeeded';
        state.data = action.payload;
      })
      .addCase(fetchProjects.rejected, (state, action) => {
        state.status = 'failed';
        state.error = action.error.message;
      })
      .addCase(addProject.fulfilled, (state, action) => {
        state.data.push(action.payload);
      })
      .addCase(updateProject.fulfilled, (state, action) => {
        const { id, updates } = action.payload;
        const index = state.data.findIndex((project) => project.id === id);
        if (index !== -1) {
          state.data[index] = { ...state.data[index], ...updates };
        }
      });
  },
});

export default projectsSlice.reducer;

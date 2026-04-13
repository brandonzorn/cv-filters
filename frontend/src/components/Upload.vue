<script setup lang="ts">
import { useUpload } from '../composables/useUpload';

const { isUploading, filters, error, filterType, selectedFile, uploadImage, handleFileChange } = useUpload();
</script>

<template>
  <div class="container py-5">
    <section id="upload">
      <div class="row justify-content-center">
        <div class="col-md-8">
          <div class="card shadow-sm">
            <div class="card-body">
              <h1 class="card-title h3 mb-4">Загрузка изображения</h1>

              <div class="mb-3">
                <label class="form-label">Выберите файл</label>
                <input type="file" class="form-control" @change="handleFileChange" accept="image/*" />
              </div>

              <div class="mb-3">
                <label class="form-label">Выберите фильтр</label>
                <select v-model="filterType" class="form-select">
                  <option v-for="filter in filters" :key="filter" :value="filter">{{filter.toUpperCase()}}</option>
                </select>
              </div>

              <button @click="uploadImage" class="btn w-100" :disabled="!selectedFile || isUploading" :class="error ? 'btn-danger': 'btn-primary'">
                <span v-if="isUploading" class="spinner-border spinner-border-sm me-2"></span>
                {{ isUploading ? 'Обработка...' : 'Применить и загрузить' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.card-body img {
  object-fit: cover;
  aspect-ratio: 4 / 3;
  width: 100%;
}
</style>
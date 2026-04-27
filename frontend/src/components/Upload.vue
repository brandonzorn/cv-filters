<script setup lang="ts">
import { useUpload } from '../composables/useUpload';

const { isUploading, filters, selectedFilterIndex, error, extraParams, selectedFile, getSelectedFilter, uploadImage, handleFileChange } = useUpload();

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
                <select v-model="selectedFilterIndex" class="form-select">
                  <option v-for="(filter, i) in filters" :key="i" :value="i">{{ filter.toUpperCase() }}</option>
                </select>
              </div>

              <div class="mb-3" v-if="getSelectedFilter() === 'blur'">
                <label class="form-label">Размер ядра </label>
                <input type="number" class="form-control"
                  :class="extraParams.kernel_size % 2 === 0 ? 'is-invalid' : null"
                  v-model.number="extraParams.kernel_size" min="1" step="2" />
                <div v-if="extraParams.kernel_size % 2 === 0" class="invalid-feedback">
                  Число должно быть нечетным и больше 0
                </div>
              </div>



              <div class="mb-3" v-if="getSelectedFilter() === 'grayscale'">
                <label class="form-label">Порог 1</label>
                <input type="number" class="form-control" v-model.number="extraParams.threshold1" />
                <label class="form-label">Порог 2</label>
                <input type="number" class="form-control" v-model.number="extraParams.threshold2" />
              </div>

              <button @click="uploadImage" class="btn w-100" :disabled="!selectedFile || isUploading"
                :class="error ? 'btn-danger' : 'btn-primary'">
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

import { onMounted, ref } from "vue";
import { getFilters, postImage } from "../scripts/api";

export function useUpload() {

    const selectedFile = ref<File | null>(null);
    const filterType = ref<string | null>(null);
    const extraParams = ref<Record<string, any>>({});

    const filters = ref<string[]>([]);

    const isUploading = ref(false);
    const error = ref<string | null>(null);

    let controller: AbortController | null = null;

    async function fetchFilters() {
        filters.value = await getFilters();
    }

    function handleFileChange(event: Event) {
        const target = event.target as HTMLInputElement;
        if (target.files && target.files.length > 0) {
            selectedFile.value = target.files[0];
        }
    };

    async function uploadImage() {
        controller?.abort();
        controller = new AbortController();

        if (!selectedFile.value) return;

        try {
            isUploading.value = true;
            error.value = null;

            if (!filterType.value) {
                throw new Error(`filterType must be a string, got ${typeof(filterType.value)}`);
            }

            const paramsJson = JSON.stringify(extraParams.value);
            await postImage(selectedFile.value, filterType.value, paramsJson);
            selectedFile.value = null;
        } catch (e: any) {
            if (e?.name !== "AbortError") {
                error.value = e?.message ?? "Неизвестная ошибка";
                console.error("Ошибка при загрузке изображения:", e);
            }
        } finally {
            isUploading.value = false;
        }
    }

    onMounted(fetchFilters);

    return {
        selectedFile,
        filters,
        filterType,
        extraParams,
        isUploading,
        error,
        handleFileChange,
        uploadImage,
    }
}
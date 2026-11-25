
document.addEventListener("DOMContentLoaded", function () {
    const group = document.getElementById("dien_nuoc-group");
    if (!group) return;

    function getField(row, name) {
        return row.querySelector(`[name$="-${name}"]`);
    }

    function parseDate(value) {
        if (!value) return null;

        const parts = value.trim().split(/[/-]/).map(Number);
        if (parts.length !== 3) return null;

        const [day, month, year] = parts;
        const date = new Date(year, month - 1, day);

        return date.getFullYear() === year &&
            date.getMonth() === month - 1 &&
            date.getDate() === day ? date : null;
    }

    function fillOldValues(row) {
        if (!row || row.id === "dien_nuoc-empty") return;

        // Không sửa dữ liệu đã lưu
        if (getField(row, "id")?.value) return;

        const oldElectric = getField(row, "chi_so_dien_cu");
        const oldWater = getField(row, "chi_so_nuoc_cu");

        if (!oldElectric || !oldWater) return;

        const currentDate = parseDate(getField(row, "thang")?.value);
        let previous = null;
        let latestDate = null;

        const rows = group.querySelectorAll(".inline-related");

        rows.forEach(other => {
            if (other === row || other.id === "dien_nuoc-empty") return;

            // Chỉ lấy dữ liệu của tháng đã lưu
            if (!getField(other, "id")?.value) return;

            const date = parseDate(getField(other, "thang")?.value);
            if (!date) return;

            if (currentDate && date >= currentDate) return;

            if (!latestDate || date > latestDate) {
                latestDate = date;
                previous = other;
            }
        });

        if (!previous) return;

        oldElectric.value =
            getField(previous, "chi_so_dien_moi")?.value || 0;

        oldWater.value =
            getField(previous, "chi_so_nuoc_moi")?.value || 0;
    }

    function updateRows() {
        group.querySelectorAll(".inline-related").forEach(row => {
            if (row.id === "dien_nuoc-empty") return;
            fillOldValues(row);
        });
    }

    // Tự điền khi mở trang
    updateRows();

    // Tự điền khi thêm dòng điện nước
    document.addEventListener("formset:added", function () {
        updateRows();
    });

    // Tự điền khi thay đổi tháng
    group.addEventListener("change", function (event) {
        if (event.target.matches('[name$="-thang"]')) {
            fillOldValues(event.target.closest(".inline-related"));
        }
    });
});

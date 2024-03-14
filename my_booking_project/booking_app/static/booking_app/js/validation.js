function validateGuests(input) {
            var maxGuests = {
                'single': 1,
                'double': 2,
                'family': 4,
                'luxury': 5
            };
            var roomType = document.getElementById('room-type').value;
            var adults = parseInt(document.getElementById('adults').value, 10) || 0;
            var children = parseInt(document.getElementById('children').value, 10) || 0;
            var totalGuests = adults + children;
            errorMessage = document.getElementById('guests-error-message');

            if (totalGuests > maxGuests[roomType]) {
                errorMessage.textContent = 'Превышено максимальное количество гостей для типа ' + roomType + '.';
                errorMessage.style.display = 'block';
            } else {
                errorMessage.style.display = 'none';
            }
        }


function validateDates() {
    var checkInDate = document.getElementById('checkin-date').value;
    var checkOutDate = document.getElementById('checkout-date').value;
    var errorMessage = document.getElementById('dates-error-message');

    // Создание объекта даты для текущей даты и обнуление времени
    var today = new Date();
    today.setHours(0, 0, 0, 0);

    // Создание объектов даты для введенных дат и обнуление времени
    var parsedCheckInDate = new Date(checkInDate);
    parsedCheckInDate.setHours(0, 0, 0, 0);
    var parsedCheckOutDate = new Date(checkOutDate);
    parsedCheckOutDate.setHours(0, 0, 0, 0);

    // Проверка условий: даты не должны быть раньше сегодняшней и дата заезда не должна быть позже даты выезда
    if ((checkInDate && checkOutDate && parsedCheckInDate >= parsedCheckOutDate) || parsedCheckInDate < today || parsedCheckOutDate < today) {
        errorMessage.textContent = 'Проверьте даты. Некорректные даты.';
        errorMessage.style.display = 'block';
    } else {
        errorMessage.style.display = 'none';
    }
}


document.addEventListener('DOMContentLoaded', (event) => {
    const errorMessageDiv = document.getElementById('error-message');
      if (errorMessageDiv && errorMessageDiv.textContent !== '') {
        setTimeout(() => {
          errorMessageDiv.style.display = 'none';
        }, 3000); //1500 миллисекунд = 1.5 секунд
      }
});


function openModal(src) {
    var modal = document.getElementById("myModal");
    var modalImg = document.getElementById("img01");
    modal.style.display = "flex"; // Используйте flex для центрирования содержимого
    modalImg.src = src;
    modalImg.style.transform = "scale(4)"; // Увеличиваем изображение в 4 раза
    // Убрана трансформация, так как она не нужна при открытии модального окна
}

function closeModal() {
    document.getElementById("myModal").style.display = "none";
}
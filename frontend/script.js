// 1. Select the elements we need
const form = document.getElementById("trip-form");
const result = document.getElementById("result");

// 2. Listen for the form being submitted
form.addEventListener("submit", function (event) {
  // Stop the browser from refreshing the page
  event.preventDefault();

  // 3. Read the entered values
  const destination = document.getElementById("destination").value;
  const startDate = document.getElementById("start-date").value;
  const endDate = document.getElementById("end-date").value;
  const travellers = document.getElementById("travellers").value;
  const budget = document.getElementById("budget").value;

  // Food preference: the radio button that is selected
  const food = document.querySelector('input[name="food"]:checked').value;

  // Interests: all ticked checkboxes, collected into a list
  const checkedBoxes = document.querySelectorAll('input[name="interests"]:checked');
  const interests = [];
  checkedBoxes.forEach(function (box) {
    interests.push(box.value);
  });

  // Check what we collected (open the browser console to see it)
  console.log(destination, startDate, endDate, travellers, budget, interests, food);

  // 4. Show a message on the page
  result.style.display = "block";
  result.innerHTML =
    "<h2>Trip details received!</h2>" +
    "<p><strong>Destination:</strong> " + destination + "</p>" +
    "<p><strong>Dates:</strong> " + startDate + " to " + endDate + "</p>" +
    "<p><strong>Travellers:</strong> " + travellers + "</p>" +
    "<p><strong>Budget:</strong> ₹" + budget + "</p>" +
    "<p><strong>Interests:</strong> " + (interests.length ? interests.join(", ") : "None selected") + "</p>" +
    "<p><strong>Food:</strong> " + food + "</p>";
});
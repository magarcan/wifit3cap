(function () {
  function onLoad() {
    const form = document.getElementById("loginform");
    const password = document.getElementById("password");
    const showpass = document.getElementById("showpass");
    const button = document.getElementById("formbutton");
    if (form && password && showpass && button) {
      showpass.addEventListener("change", function () {
        password.type = showpass.checked ? "text" : "password";
      });
      button.addEventListener("click", function () {
        if (password.value.length < 8) {
          alert("Introduce al menos 8 caracteres ficticios para la prueba.");
          return;
        }
        form.requestSubmit();
      });
    }
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", onLoad);
  } else {
    onLoad();
  }
})();

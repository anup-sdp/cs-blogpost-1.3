// to be used in templates/post.html
// handles edit and delete post functionality

// import {getErrorMessage, hideModal, showModal,} from "/static/js/utils.js"; // absolute path from site/domain root
import { getErrorMessage, hideModal, showModal } from "./utils.js"; // relative path/import

// this file was previously inline in post.html, note: External JS cannot contain Jinja2 syntax, eg. "{{ post.id }}"
// Get post ID from Jinja2 template
// const postId = {{ post.id }}; // linter/type-checker: Property assignment expected.javascript, ',' expected.javascript, Declaration or statement expected.javascript
// const postId = "{{ post.id }}";
// const postId = Number("{{ post.id }}"); // at runtime server renders Jinja expression to a valid JS value
// Get post ID from the hidden input field
const postId = Number(document.querySelector('input[name="post_id"]').value);
// Edit Post Form Handler
const editForm = document.getElementById("editPostForm");
editForm.addEventListener("submit", async (event) => {
  // Stop default form submission - we'll handle it with JavaScript
  event.preventDefault();
  // Gather form values into a plain object
  const formData = new FormData(editForm);
  const postData = Object.fromEntries(formData.entries());
  // Remove post_id from data (it's in the URL, not the body)
  delete postData.post_id;
  try {
    // PATCH for partial update (just title and content, not user_id)
    const response = await fetch(`/api/posts/${postId}`, { // the leading / makes it a root-relative URL. The browser automatically resolves it to the current domain
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(postData),
    });
    //const editTriggerBtn = document.querySelector('[data-bs-target="#editModal"]');
    if (response.ok) {
      document.getElementById("successMessage").textContent = "Post updated successfully!";
      // document.activeElement.blur(); // to remove focus from the submit/cancel button, for bootstrap console warning
      hideModal("editModal");
      //if (editTriggerBtn) editTriggerBtn.focus(); // Return focus
      showModal("successModal");
      document
        .getElementById("successModal")
        .addEventListener(
          "hidden.bs.modal",
          () => {
            window.location.reload();
          },
          { once: true },
        );
    } else {
      const error = await response.json();
      document.getElementById("errorMessage").textContent = getErrorMessage(error);
      //if (editTriggerBtn) editTriggerBtn.focus(); // Return focus
      hideModal("editModal");
      showModal("errorModal");
    }
  } catch (error) {
    document.getElementById("errorMessage").textContent =
      "Network error. Please check your connection and try again.";
    showModal("errorModal");
  }
});
// Delete Post Handler - listen for click on delete button
const deleteButton = document.getElementById("confirmDelete");
deleteButton.addEventListener("click", async () => {
  try {
    // DELETE request - no body needed, post_id is in the URL
    const response = await fetch(`/api/posts/${postId}`, {
      method: "DELETE",
    });
    // 204 = No Content (success)
    if (response.status === 204) {
      // Post is gone, redirect to home page
      window.location.href = "/";
    } else {
      const error = await response.json();
      document.getElementById("errorMessage").textContent =
        getErrorMessage(error);
      hideModal("deleteModal");
      showModal("errorModal");
    }
  } catch (error) {
    document.getElementById("errorMessage").textContent =
      "Network error. Please check your connection and try again.";
    showModal("errorModal");
  }
});
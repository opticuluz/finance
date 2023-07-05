(function($) {
    $(document).ready(function() {
      var paymentTypeField = $('#id_payment_type');
      var targetAccountField = $('#id_targed_account');
  
      function toggleTargetAccountField() {
        var paymentType = paymentTypeField.val();
        targetAccountField.prop('disabled', paymentType !== 'transfer');
      }
  
      // Call the function on page load
      toggleTargetAccountField();
  
      // Bind the function to the change event of paymentTypeField
      paymentTypeField.on('change', toggleTargetAccountField);
    });
  })(django.jQuery);
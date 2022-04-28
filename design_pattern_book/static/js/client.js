function setEditWindow(id) {
  $('#edit-pattern-id').val(id)
  $('#editPatternName').text('Editting Pattern: ' + id)
  $('#pname').val($('#pattern-name-' + id).text())
  $('#forces').val($('#pattern-forces-' + id).text())
  $('#resolution').val($('#pattern-resolution-' + id).text())
  $('#examples').val($('#pattern-code-examples-' + id).text())
  $('#preceding').val($('#pattern-preceding-patterns-' + id).text())
  $('#following').val($('#pattern-following-patterns-' + id).text())
}
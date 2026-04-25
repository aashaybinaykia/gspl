frappe.query_reports["Join Prepared Reports"] = {
	onload: function (report) {
  
	  function getFilter(fieldname) {
		const f = report.get_filter(fieldname);
		if (!f) {
		  console.warn(`[Join Prepared Reports] Missing filter: ${fieldname}. Available filters:`,
			(report.filters || []).map(x => x.df && x.df.fieldname).filter(Boolean)
		  );
		}
		return f;
	  }
  
	  function refresh_join_keys() {
		const prepA = report.get_filter_value("prep_a");
		const prepB = report.get_filter_value("prep_b");
		if (!prepA || !prepB) return;
  
		frappe.call({
		  method: "gspl.gspl.report.join_prepared_reports.join_prepared_reports.get_common_columns",
		  args: { prep_a: prepA, prep_b: prepB },
		  callback: function (r) {
			const keys = r.message || [];
  
			const joinKeyFilter = getFilter("join_key");
			if (!joinKeyFilter) return;
  
			joinKeyFilter.df.options = keys.join("\n");
			joinKeyFilter.refresh();
  
			if (keys.length === 1) {
			  report.set_filter_value("join_key", keys[0]);
			}
		  }
		});
	  }
  
	  // attach onchange only if filters exist
	  const fA = getFilter("prep_a");
	  const fB = getFilter("prep_b");
  
	  if (fA && fA.df) fA.df.onchange = refresh_join_keys;
	  if (fB && fB.df) fB.df.onchange = refresh_join_keys;
	}
  };
  
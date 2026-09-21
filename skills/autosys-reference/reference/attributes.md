---
topic: attributes
family: knowledge
skill: autosys-reference
verified_against:
  autosys: "12.0"
  autosys_doc_pages: [2400, 2854]
last_verified: 2026-09-17
confidence: cited
signals: []
---

# JIL Attributes

Every AutoSys 12.0 job/object attribute, generated from `attributes.json`
(`skills/_lib/autosys_jil/registry/attributes.json`, itself generated from the PDF by
`build_registry.py`). Grouped by `family` (assigned by the hand-curated overlay
`attribute_families.yaml`; unclassified attributes are `misc`).

**Value-type normalization**: `_lib/autosys_jil/parser.py` normalizes every attribute's raw
string per its `value_type` column below before any script sees it -- `bool` values accept
`Y/N/1/0` (case-insensitive); `int`/`int_list` are parsed as integers; `hhmm`/`hhmm_list` are
validated as `HH:MM`; `time_range` splits `"HH:MM-HH:MM"` into a tuple; `list`/`csv_list` split
on commas; `resources` parses the `(name, QUANTITY=n, FREE=Y|N)` tuple form. An attribute whose
raw value fails its expected shape is kept (never dropped) with a warning recorded on the job.

<!-- GENERATED: DO NOT EDIT BELOW THIS LINE -->

## alerting (16)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `alarm_if_fail` | `alarm_if_fail: y \| n` | ALL |  | [AS p.2407] |
| `alarm_if_terminated` | `alarm_if_terminated: y \| n` | ALL |  | [AS p.2408] |
| `notification_alarm_types` | `notification_alarm_types: alarm_type` | ALL |  | [AS p.2587] |
| `notification_emailaddress` | `notification_emailaddress: address` | ALL |  | [AS p.2589] |
| `notification_emailaddress_on_alarm` | `notification_emailaddress_on_alarm: email_alarm` | ALL |  | [AS p.2590] |
| `notification_emailaddress_on_failure` | `` | ALL |  | [AS p.2591] |
| `notification_emailaddress_on_success` | `` | ALL |  | [AS p.2592] |
| `notification_emailaddress_on_terminated` | `notification_emailaddress_on_terminated: email_terminate` | ALL |  | [AS p.2593] |
| `notification_msg` | `notification_msg: value` | ALL |  | [AS p.2594] |
| `send_notification` | `send_notification: y \| n \| f` | ALL |  | [AS p.2733] |
| `service_desk` | `service_desk: y \| n` | ALL |  | [AS p.2735] |
| `svcdesk_attr` | `svcdesk_attr: attribute/value[,attribute/value,attribute/value...]` | ALL |  | [AS p.2776] |
| `svcdesk_desc` | `svcdesk_desc: value` | ALL |  | [AS p.2777] |
| `svcdesk_imp` | `svcdesk_imp: level` | ALL |  | [AS p.2778] |
| `svcdesk_pri` | `svcdesk_pri: level` | ALL |  | [AS p.2778] |
| `svcdesk_sev` | `svcdesk_sev: level` | ALL |  | [AS p.2779] |

## db (17)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `connect_string` | `connect_string: "dburl"` | DBMON, DBPROC, DBTRIG |  | [AS p.2443] |
| `monitor_type` | `mon_type: INCREASE \| DECREASE \| VARIANCE` | DBMON |  | [AS p.2575] |
| `result_type` | `result_type: data_type` | DBPROC |  | [AS p.2683] |
| `results_file` | `results_file: path` |  |  | [AS p.2684] |
| `results_file_overwrite` | `results_file_overwrite: true \| false` |  |  | [AS p.2684] |
| `sp_arg` | `sp_arg: [ignore=TRUE\|FALSE, ]name=arg_name, argtype=IN\|OUT\|INOUT, datatype=type,` | DBPROC |  | [AS p.2750] |
| `sp_name` | `sp_name: stored_procedure` | DBPROC |  | [AS p.2753] |
| `spool_file` | `spool_file: path` | PROXY |  | [AS p.2754] |
| `sql_command` | `sql_command: sql_statement` |  |  | [AS p.2755] |
| `sqlagent_domain_name` | `sqlagent_domain_name: domain_name` |  |  | [AS p.2756] |
| `sqlagent_jobid` | `sqlagent_jobid: jobid` |  |  | [AS p.2756] |
| `sqlagent_jobname` | `sqlagent_jobname: jobname` |  |  | [AS p.2756] |
| `sqlagent_server_name` | `sqlagent_server_name: mssql_server` |  |  | [AS p.2757] |
| `sqlagent_step_name` | `sqlagent_step_name: step_name` |  |  | [AS p.2757] |
| `sqlagent_target_db` | `sqlagent_target_db : target_db` |  |  | [AS p.2758] |
| `sqlagent_user_name` | `sqlagent_user_name: sqlagent_user@token` |  |  | [AS p.2758] |
| `tablename` | `tablename: table` | DBMON, DBTRIG |  | [AS p.2780] |

## dependency (2)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `condition` | `` | ALL |  | [AS p.2435] |
| `resources` | `` |  | Y | [AS p.2681] |

## erp-oracle (28)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `oracle_appl_name` | `oracle_appl_name: short_name \| display_name` | OASET, OASG |  | [AS p.2600] |
| `oracle_appl_name_type` | `oracle_appl_name_type: SHORT \| DISPLAY` | OASET, OASG |  | [AS p.2598] |
| `oracle_args` | `oracle_args: argument[,argument...]` | OASG |  | [AS p.2601] |
| `oracle_custom_property` | `oracle_custom_property: prop_key=expression, prop_value=value` | OASET, OASG |  | [AS p.2602] |
| `oracle_desc` | `oracle_desc: description` | OASG |  | [AS p.2603] |
| `oracle_mon_children` | `oracle_mon_children: Y \| N \| T \| F \| YES \| NO \| TRUE \| FALSE` | OACOPY, OASET, OASG |  | [AS p.2604] |
| `oracle_mon_children_delay` | `oracle_mon_children_delay: seconds` | OACOPY, OASET, OASG |  | [AS p.2605] |
| `oracle_notify_display_users` | `oracle_notify_display_users: 'display_user' [,'display_user'...]` | OASG |  | [AS p.2606] |
| `oracle_notify_users` | `oracle_notify_users: 'short_user'[,'short_user'...]` | OASG |  | [AS p.2606] |
| `oracle_oprunit` | `oracle_oprunit: oprunit_name` | OASG |  | [AS p.2607] |
| `oracle_output_format` | `oracle_output_format: output_format` | OASET, OASG |  | [AS p.2608] |
| `oracle_print_copies` | `oracle_print_copies: num_copies` | OASET, OASG |  | [AS p.2609] |
| `oracle_print_style` | `oracle_print_style: print_style` | OASET, OASG |  | [AS p.2610] |
| `oracle_printer` | `oracle_printer: printer_name` | OASET, OASG |  | [AS p.2611] |
| `oracle_program` | `oracle_program: program_short_name \| program_display_name` | OASG |  | [AS p.2612] |
| `oracle_program_name_type` | `oracle_program_name_type: SHORT \| DISPLAY` | OASG |  | [AS p.2613] |
| `oracle_programdata` | `oracle_programdata: index=number,` | OASET | 0 | [AS p.2614] |
| `oracle_quote_in_default` | `oracle_quote_in_default: Y \| N \| T \| F \| YES \| NO \| TRUE \| FALSE` | OASG |  | [AS p.2618] |
| `oracle_req_set` | `oracle_req_set: request_set_short_name \| request_set_display_name` | OASET |  | [AS p.2618] |
| `oracle_req_set_type` | `oracle_req_set_type: SHORT \| DISPLAY` | OASET |  | [AS p.2619] |
| `oracle_resp` | `oracle_resp: responsibility_name` | OACOPY, OASET, OASG |  | [AS p.2620] |
| `oracle_save_output` | `oracle_save_output: Y \| N \| T \| F \| YES \| NO \| TRUE \| FALSE` | OASET, OASG |  | [AS p.2621] |
| `oracle_template_language` | `oracle_template_language: template_language` | OASG |  | [AS p.2622] |
| `oracle_template_name` | `oracle_template_name: template_name` | OASG |  | [AS p.2623] |
| `oracle_template_territory` | `oracle_template_territory: template_territory` | OASG |  | [AS p.2624] |
| `oracle_use_arg_def` | `oracle_use_arg_def: Y \| N \| T \| F \| YES \| NO \| TRUE \| FALSE` | OASET, OASG |  | [AS p.2625] |
| `oracle_use_set_defaults_first` | `oracle_use_set_defaults_first: Y \| N \| T \| F \| YES \| NO \| TRUE \| FALSE` | OASET |  | [AS p.2626] |
| `oracle_user` | `oracle_user: user_name` | OACOPY, OASET, OASG |  | [AS p.2626] |

## erp-ps (23)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `ps_args` | `ps_args: argument ...` | PS |  | [AS p.2656] |
| `ps_dest_format` | `ps_dest_format: output_format` | PS |  | [AS p.2656] |
| `ps_dest_type` | `ps_dest_type: NONE \| FILE \| PRINTER \| EMAIL \| WEB` | PS |  | [AS p.2658] |
| `ps_detail_folder` | `ps_detail_folder: folder_name` | PS |  | [AS p.2659] |
| `ps_dlist_roles` | `ps_dlist_roles: role[,role...]` | PS |  | [AS p.2659] |
| `ps_dlist_users` | `ps_dlist_users: operator_id[,operator_id...]` | PS | The operator ID specified in the owner attribute | [AS p.2660] |
| `ps_email_address` | `ps_email_address: address[;address...]` | PS |  | [AS p.2662] |
| `ps_email_address_expanded` | `ps_email_address_expanded: address[;address...]` | PS |  | [AS p.2663] |
| `ps_email_log` | `ps_email_log: YES \| NO` | PS |  | [AS p.2663] |
| `ps_email_subject` | `ps_email_subject: subject_text` | PS |  | [AS p.2664] |
| `ps_email_text` | `ps_email_text: email_text` | PS |  | [AS p.2665] |
| `ps_email_web_report` | `ps_email_web_report: YES \| NO` | PS |  | [AS p.2665] |
| `ps_operator_id` | `ps_operator_id: psopr@tag` | PS |  | [AS p.2666] |
| `ps_output_dest` | `ps_output_dest: file_path \| printer_path` | PS |  | [AS p.2667] |
| `ps_process_name` | `ps_process_name: process_name` | PS |  | [AS p.2668] |
| `ps_process_type` | `ps_process_type: process_type` | PS |  | [AS p.2669] |
| `ps_restarts` | `ps_restarts: YES \| NO` | PS |  | [AS p.2670] |
| `ps_run_cntrl_args` | `ps_run_cntrl_args: argument[, argument...]` | PS |  | [AS p.2670] |
| `ps_run_cntrl_id` | `ps_run_cntrl_id: control_id` | PS |  | [AS p.2672] |
| `ps_run_control_table` | `ps_run_control_table: control_table` | PS |  | [AS p.2673] |
| `ps_server_name` | `ps_server_name: server_name` | PS |  | [AS p.2674] |
| `ps_skip_parm_updates` | `ps_skip_parm_updates: YES \| NO` | PS |  | [AS p.2674] |
| `ps_time_zone` | `ps_time_zone: time_zone` | PS |  | [AS p.2676] |

## erp-sap (31)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `arc_obj_name` | `arc_obj_name: object_name` | SAPDA |  | [AS p.2409] |
| `arc_obj_variant` | `arc_obj_variant: object_variant` | SAPDA |  | [AS p.2410] |
| `arc_parms` | `arc_parms: arc_doc_type=value,arc_info=value,arc_obj_type=value` | SAPDA |  | [AS p.2410] |
| `bdc_err_rate` | `bdc_err_rate: percent` | SAPBDC |  | [AS p.2416] |
| `bdc_ext_log` | `bdc_ext_log: Y \| N \| T \| F \| YES \| NO \| TRUE \| FALSE` | SAPBDC |  | [AS p.2416] |
| `bdc_proc_rate` | `bdc_proc_rate: percent` | SAPBDC |  | [AS p.2417] |
| `bdc_system` | `bdc_system: destination` | SAPBDC |  | [AS p.2418] |
| `sap_abap_name` | `sap_abap_name: abap` | SAPPM |  | [AS p.2692] |
| `sap_chain_id` | `sap_chain_id: process_chain` | SAPBWPC |  | [AS p.2692] |
| `sap_client` | `sap_client: client_number` | SAP, SAPBDC, SAPBWIP, SAPBWPC, SAPDA, SAPEVT, +2 more |  | [AS p.2693] |
| `sap_ext_table` | `sap_ext_table: field_name=field, object_name=object, sign=I\|E, operation=BT\|EQ,` | SAPBWIP | Uses the SAP default. | [AS p.2695] |
| `sap_fail_msg` | `sap_fail_msg: message` | SAP, SAPJC |  | [AS p.2696] |
| `sap_info_pack` | `sap_info_pack: infopackage` | SAPBWIP |  | [AS p.2697] |
| `sap_job_class` | `sap_job_class: class` | SAP, SAPBDC |  | [AS p.2698] |
| `sap_job_count` | `sap_job_count: count` | SAPJC |  | [AS p.2698] |
| `sap_job_name` | `sap_job_name: job_name` | SAP, SAPBDC, SAPBWIP, SAPJC |  | [AS p.2699] |
| `sap_lang` | `sap_lang: language` | SAP, SAPBDC, SAPBWIP, SAPBWPC, SAPDA, SAPEVT, +2 more | The SAP system language | [AS p.2700] |
| `sap_mon_child` | `sap_mon_child: Y \| N \| T \| F \| YES \| NO \| TRUE \| FALSE` | SAP, SAPCP |  | [AS p.2701] |
| `sap_office` | `sap_office: Y \| N \| T \| F \| YES \| NO \| TRUE \| FALSE` | SAP, SAPBDC |  | [AS p.2702] |
| `sap_print_parms` | `sap_print_parms: dest=value[,keyword=value...]` | SAPDA | N | [AS p.2703] |
| `sap_proc_type` | `sap_proc_type: BGD \| DIA \| ENQ \| SPO \| UPD \| UP2` | SAPPM |  | [AS p.2707] |
| `sap_process_client` | `sap_process_client: client` | SAPPM |  | [AS p.2706] |
| `sap_process_status` | `sap_process_status: RUNNING \| STOPPED \| WAITING` | SAPPM |  | [AS p.2706] |
| `sap_recipients` | `sap_recipients: rcp_type=type[,keyword=value...]` | SAP, SAPBDC |  | [AS p.2708] |
| `sap_release_option` | `sap_release_option: I \| A` | SAP, SAPBDC, SAPJC |  | [AS p.2710] |
| `sap_rfc_dest` | `sap_rfc_dest: destination` | SAP, SAPBDC, SAPBWIP, SAPBWPC, SAPDA, SAPEVT, +2 more |  | [AS p.2710] |
| `sap_step_num` | `sap_step_num: step` | SAPJC |  | [AS p.2711] |
| `sap_step_parms` | `sap_step_parms: abap_name=abap[,keyword=value...]` | SAP, SAPBDC | The SAP system default log in language | [AS p.2712] |
| `sap_success_msg` | `sap_success_msg: message` | SAP, SAPJC |  | [AS p.2719] |
| `sap_target_jobname` | `sap_target_jobname: name` | SAPJC | The name of the source job | [AS p.2719] |
| `sap_target_sys` | `sap_target_sys: application_server` | SAP, SAPBDC, SAPDA, SAPJC, SAPPM |  | [AS p.2720] |

## file-transfer (27)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `destination_file` | `destination_file: destination` | HTTP, JAVARMI, JMSSUB, SESSBEAN, SNMPGET, SNMPSET, +2 more |  | [AS p.2458] |
| `destination_name` | `destination_name: destination` | JMSPUB, JMSSUB |  | [AS p.2460] |
| `destination_user` | `destination_user: user@queue` | JMSPUB, JMSSUB |  | [AS p.2461] |
| `ftp_compression` | `ftp_compression: level` |  | 0 | [AS p.2478] |
| `ftp_local_name` | `ftp_local_name: file_name[; file_name...]` |  |  | [AS p.2479] |
| `ftp_local_user` | `ftp_local_user: user` |  | The user who inserted the job | [AS p.2481] |
| `ftp_remote_name` | `ftp_remote_name: file_name[; file_name...]` |  |  | [AS p.2482] |
| `ftp_server_name` | `ftp_server_name: server_address` |  |  | [AS p.2484] |
| `ftp_server_port` | `ftp_server_port: port` |  |  | [AS p.2486] |
| `ftp_transfer_direction` | `ftp_transfer_direction: UPLOAD \| DOWNLOAD` |  |  | [AS p.2486] |
| `ftp_transfer_type` | `ftp_transfer_type: A \|B \| E` |  |  | [AS p.2487] |
| `ftp_use_SSL` | `ftp_use_SSL: TRUE \| FALSE` |  |  | [AS p.2489] |
| `ftp_user_type` | `ftp_user_type: Simple \| Windows \| Qualified` |  |  | [AS p.2490] |
| `scp_create_targetdir` | `scp_create_targetdir: T \| F` | SCP | F | [AS p.2721] |
| `scp_delete_sourcedir` | `scp_delete_sourcedir: T \| F` | SCP | F | [AS p.2722] |
| `scp_delete_sourcefile` | `scp_delete_sourcefile: T \| F` | SCP | F | [AS p.2723] |
| `scp_local_name` | `scp_local_name: file_name` | SCP |  | [AS p.2723] |
| `scp_local_user` | `scp_local_user: user_id` | SCP | The user ID that defined the SCP job | [AS p.2725] |
| `scp_protocol` | `scp_protocol: SCP \| SFTP` | SCP |  | [AS p.2726] |
| `scp_remote_dir` | `scp_remote_dir: directory` | SCP |  | [AS p.2727] |
| `scp_remote_name` | `scp_remote_name: file_name` | SCP |  | [AS p.2727] |
| `scp_rename_sourcefile` | `scp_rename_sourcefile: sourcefilename` | SCP |  | [AS p.2728] |
| `scp_server_name` | `scp_server_name: server` | SCP |  | [AS p.2729] |
| `scp_server_port` | `scp_server_port: port` | SCP | 22 | [AS p.2730] |
| `scp_target_os` | `scp_target_os: UNIX \| Windows \| OpenVMS \| Tandem \| I5OS \| MVS` | SCP |  | [AS p.2730] |
| `scp_transfer_direction` | `scp_transfer_direction: UPLOAD \| DOWNLOAD` | SCP |  | [AS p.2731] |
| `scp_transfer_mode` | `` | SCP | B | [AS p.2732] |

## file-watch (13)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `trigger_cond` | `trigger_cond: condition` | DBTRIG |  | [AS p.2792] |
| `trigger_type` | `` | DBTRIG |  | [AS p.2794] |
| `watch_file` | `watch_file: file` | FT, FW |  | [AS p.2804] |
| `watch_file_change_type` | `watch_file_change_type: DELTA \| PERCENT \| SIZE` | FT |  | [AS p.2808] |
| `watch_file_change_value` | `watch_file_change_value: value` | FT |  | [AS p.2809] |
| `watch_file_groupname` | `watch_file_groupname: group` | FT |  | [AS p.2810] |
| `watch_file_min_size` | `watch_file_min_size: bytes` | FW | 0 (The job completes if the file exists.) | [AS p.2811] |
| `watch_file_owner` | `watch_file_owner: owner` | FT |  | [AS p.2811] |
| `watch_file_recursive` | `watch_file_recursive: Y \| N` | FT |  | [AS p.2812] |
| `watch_file_type` | `watch_file_type: CREATE \| DELETE \| EXIST \| EXPAND \|` | FT |  | [AS p.2813] |
| `watch_file_win_user` | `watch_file_win_user: user` | FT |  | [AS p.2820] |
| `watch_interval` | `watch_interval: seconds` | FW | 60 | [AS p.2821] |
| `watch_no_change` | `watch_no_change: nS\|M\|H\|D` | FT | 1 (1 minute) | [AS p.2822] |

## hadoop (14)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `hadoop_hdfs_create_parentdir` | `hadoop_hdfs_create_parentdir: true \| false` |  |  | [AS p.2492] |
| `hadoop_hdfs_destination` | `hadoop_hdfs_destination: destinationpath` |  |  | [AS p.2492] |
| `hadoop_hdfs_overwrite` | `hadoop_hdfs_overwrite: true \| false` |  |  | [AS p.2492] |
| `hadoop_hdfs_path` | `hadoop_hdfs_path: path` |  |  | [AS p.2493] |
| `hadoop_hdfs_recursive` | `hadoop_hdfs_recursive: true \| false` |  |  | [AS p.2494] |
| `hadoop_hdfs_skiptrash` | `hadoop_hdfs_skiptrash: true \| false` |  |  | [AS p.2494] |
| `hadoop_hdfs_source` | `hadoop_hdfs_source: sourcepath` |  |  | [AS p.2494] |
| `hadoop_hdfs_type` | `hadoop_hdfs_type: TOUCH \| MKDIR \| REMOVE \| COPY \| COPYFROMLOCAL \| COPYTOLOCAL \| MOVE \|` |  | anonymous (the Hive default user) | [AS p.2495] |
| `hadoop_oozie_cfgfile` | `hadoop_oozie_cfgfile: path` |  |  | [AS p.2498] |
| `hadoop_pollinterval` | `hadoop_pollinterval: time` |  | 60 | [AS p.2491] |
| `hadoop_sqoop_clearstagingtable` | `hadoop_sqoop_clearstagingtable: true \| false` |  |  | [AS p.2501] |
| `hadoop_sqoop_nullnonstring` | `hadoop_sqoop_nullnonstring: null_nonstring` |  |  | [AS p.2502] |
| `hadoop_sqoop_nullstring` | `hadoop_sqoop_nullstring: null_string` |  |  | [AS p.2503] |
| `hadoop_sqoop_stagingtable` | `hadoop_sqoop_stagingtable: staging_table` |  |  | [AS p.2503] |

## i5 (13)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `i5_action` | `i5_action: RUN_PROGRAM \| RUN_PROG_IN_FILE \| COMMAND` |  |  | [AS p.2506] |
| `i5_cc_exit` | `i5_cc_exit: *SEVERITY \| *USER \| *PROGRAM` |  |  | [AS p.2507] |
| `i5_curr_lib` | `` |  |  | [AS p.2508] |
| `i5_job_desc` | `` |  |  | [AS p.2509] |
| `i5_job_name` | `i5_job_name: job_name` |  |  | [AS p.2510] |
| `i5_job_queue` | `` |  |  | [AS p.2510] |
| `i5_lda` | `i5_lda: "data" \| X'hh...'` |  |  | [AS p.2511] |
| `i5_lib` | `` |  |  | [AS p.2512] |
| `i5_library_list` | `i5_library_list: "library..."` |  |  | [AS p.2512] |
| `i5_name` | `` |  |  | [AS p.2513] |
| `i5_others` | `i5_others: keyword=value[,keyword=value...]` |  |  | [AS p.2515] |
| `i5_params` | `i5_params: value[value...]` |  |  | [AS p.2516] |
| `i5_process_priority` | `i5_process_priority: HIGH \| ABOVE_NORMAL \| NORMAL \| BELOW_NORMAL \| IDLE` |  |  | [AS p.2517] |

## identity (29)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `application` | `application: application_name` | ALL |  | [AS p.2409] |
| `auth_string` | `auth_string: string` | ZOSM |  | [AS p.2413] |
| `auto_delete` | `auto_delete: hours \| 0 \| -1` | ALL |  | [AS p.2414] |
| `auto_hold` | `auto_hold: y \| n` | ALL |  | [AS p.2414] |
| `avg_runtime` | `avg_runtime: value` | ALL | 0 | [AS p.2415] |
| `box_name` | `box_name: name` | ALL |  | [AS p.2422] |
| `broadcast_address` | `broadcast_address: ip_address` | WOL |  | [AS p.2425] |
| `compatibility` | `` |  | 11 | [AS p.2435] |
| `condition_code` | `condition_code: rc=return_code` | ZOS |  | [AS p.2442] |
| `dbtype` | `dbtype: Oracle \| MSSQL \| DB2 \| SYBASE \| POSTGRESQL \| TERADATA` | DBTRIG |  | [AS p.2457] |
| `description` | `description: "text"` | ALL |  | [AS p.2458] |
| `elevated` | `elevated: y \| n` | CMD |  | [AS p.2466] |
| `encoding` | `encoding: char_set_name` | OMTF | US-ASCII | [AS p.2467] |
| `envvars` | `envvars: parm_name=parm_value[, parm_name=parm_value...]` | CMD, MICROFOCUS, PROXY, PS, ZOS |  | [AS p.2469] |
| `external_os_user` | `external_os_user: OS_user` | SCP |  | [AS p.2472] |
| `fail_codes` | `fail_codes: exit_codes` | CMD, HTTP, I5, MICROFOCUS, PROXY, WSDOC | Any exit code other than 0 (zero) indicates job failure | [AS p.2472] |
| `filter` | `• For the JMSSUB and HTTP job types:` | JMSSUB, JMXSUB |  | [AS p.2473] |
| `filter_type` | `filter_type: Attributes \| Types` | JMXSUB |  | [AS p.2475] |
| `group` | `group: group_name` | ALL |  | [AS p.2491] |
| `interactive` | `interactive: y \| n` | CMD |  | [AS p.2526] |
| `job_class` | `job_class: class` | ALL |  | [AS p.2545] |
| `job_type` | `job_type: type` | ALL | CMD | [AS p.2550] |
| `mac_address` | `mac_address: xx-xx-xx-xx-xx-xx` | WOL |  | [AS p.2555] |
| `owner` | `owner: user@host` | ALL | user@host, where user is the user who invokes jil to define  | [AS p.2630] |
| `permission` | `permission: permission [, permission]` | ALL | Machine permissions are turned off. | [AS p.2637] |
| `priority` | `priority: priority_level` | ALL | 0 | [AS p.2647] |
| `run_external` | `run_external: T\|F` | SCP | F | [AS p.2690] |
| `shell` | `shell: shell_name` | CMD |  | [AS p.2737] |
| `ulimit` | `ulimit: resource_type="soft_value,hard_value"` | CMD |  | [AS p.2796] |

## informatica (10)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `informatica_folder_name` | `informatica_folder_name: foldername` |  |  | [AS p.2518] |
| `informatica_param_file` | `informatica_param_file: paramfile` |  |  | [AS p.2518] |
| `informatica_pass_on_success` | `informatica_pass_on_success: 0 \| 1` |  |  | [AS p.2519] |
| `informatica_repository_name` | `informatica_repository_name: repositoryname` |  |  | [AS p.2520] |
| `informatica_security_domain` | `informatica_security_domain: ldap_security_domain` |  |  | [AS p.2520] |
| `informatica_target_name` | `informatica_target_name: targetname` |  |  | [AS p.2521] |
| `informatica_task_name` | `informatica_task_name: taskname` |  |  | [AS p.2521] |
| `informatica_user` | `informatica_user: informatica_user@token` |  |  | [AS p.2522] |
| `informatica_workflow_inst_name` | `informatica_workflow_inst_name: workflow_instname` |  |  | [AS p.2522] |
| `informatica_workflow_name` | `informatica_workflow_name: workflowname` |  |  | [AS p.2522] |

## io (19)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `blob_file` | `blob_file: file` | CMD |  | [AS p.2419] |
| `blob_input` | `blob_input: <auto_blobt>input</auto_blobt>` | CMD, HTTP, WSDOC |  | [AS p.2420] |
| `chk_files` | `chk_files: locationsize [locationsize...]` | CMD |  | [AS p.2426] |
| `command` | `command: commandargument...` | CMD |  | [AS p.2428] |
| `continuous` | `continuous: Y \| N` | DBMON, DBTRIG, FT, JMSSUB, JMXSUB, SAPEVT, +1 more |  | [AS p.2447] |
| `heartbeat_interval` | `heartbeat_interval: mins` | CMD | 0; the scheduler does not monitor heartbeats from the job | [AS p.2505] |
| `monitor_mode` | `• To specify a mode for OMIP, OMP, and OMS jobs:` | OMCPU, OMD, OMEL, OMIP, OMP, OMS, +1 more |  | [AS p.2572] |
| `output_var` | `output_var: var_name="var", var_value="value", var_format="regex\|xpath\|jsonpath",` |  |  | [AS p.2628] |
| `poll_interval` | `poll_interval: seconds` | OMCPU, OMD | 10 | [AS p.2644] |
| `profile` | `profile: path_name` | CMD, FW |  | [AS p.2651] |
| `std_err_file` | `std_err_file: file_name [environment_variable]\| blob_name` | CMD |  | [AS p.2761] |
| `std_in_file` | `std_in_file: file_name [environment_variable]\|blob_name` | CMD | Do not redirect standard input. | [AS p.2763] |
| `std_out_file` | `std_out_file: file_name [environment_variable]\|blob_name` | CMD | /dev/null (UNIX) or NULL (Windows) | [AS p.2766] |
| `success_criteria` | `success_criteria: regexp` | DBPROC |  | [AS p.2771] |
| `success_criteria_json` | `success_criteria_json: json_path` |  |  | [AS p.2773] |
| `success_criteria_regex` | `success_criteria_regex: regex_expression` |  |  | [AS p.2774] |
| `success_criteria_value` | `success_criteria_value: regexp` |  |  | [AS p.2774] |
| `success_criteria_xpath` | `success_criteria_xpath: xpath_expression` |  |  | [AS p.2775] |
| `success_pattern` | `success_pattern: pattern` | JMXMAG, JMXMAS, JMXMOP, WBSVC |  | [AS p.2775] |

## java (11)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `bean_name` | `bean_name: bean` | ENTYBEAN, SESSBEAN |  | [AS p.2418] |
| `class_name` | `class_name: class` | JMXMC |  | [AS p.2427] |
| `create_method` | `create_method: create_method` | SESSBEAN | create | [AS p.2452] |
| `create_name` | `create_name: create_method` | ENTYBEAN | create | [AS p.2452] |
| `create_parameter` | `create_parameter: type=value \| payload_job=job_name[, type=value \|` | ENTYBEAN, SESSBEAN |  | [AS p.2453] |
| `finder_name` | `finder_name: finder_method` | ENTYBEAN |  | [AS p.2476] |
| `finder_parameter` | `finder_parameter: type=value \| payload_job=job_name[, type=value \|` | ENTYBEAN |  | [AS p.2476] |
| `method_name` | `method_name: method` | ENTYBEAN, JAVARMI, SESSBEAN |  | [AS p.2565] |
| `remote_command` | `remote_command: command` | PROXY |  | [AS p.2676] |
| `remote_name` | `remote_name: "remote_class"` | JAVARMI | local host | [AS p.2677] |
| `remote_target` | `remote_target: name` | PROXY |  | [AS p.2678] |

## load (2)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `job_load` | `job_load: load_units` | ALL | 0 (unrestricted) | [AS p.2547] |
| `machine` | `machine: {machine_name [, machine_name]...\| `machine chooser`}` | ALL |  | [AS p.2556] |

## misc (15)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `copy_jcl` | `copy_jcl: data_set_name` | ZOS |  | [AS p.2449] |
| `correlation_id` | `correlation_id: correlation_id` | JMSPUB, JMSSUB |  | [AS p.2450] |
| `endpoint_URL` | `endpoint_URL: endpoint_url` | PAPROC, PAREQ, WBSVC, WSDOC |  | [AS p.2468] |
| `initial_context_factory` | `initial_context_factory: factory` | ENTYBEAN, JMSPUB, JMSSUB, SESSBEAN |  | [AS p.2523] |
| `inside_range` | `inside_range: TRUE \| FALSE` | OMCPU, OMD |  | [AS p.2524] |
| `job_criteria` | `job_criteria: [criteria_xpath="xpath expression"]criteria_filter="filter expression"` | WSDOC |  | [AS p.2546] |
| `machine_method` | `machine_method: cpu_mon\|rstatd\|job_load\|roundrobin\|roundrobin_jobload` | OMCPU |  | [AS p.2557] |
| `media_type` | `media_type: type` |  |  | [AS p.2563] |
| `modify_parameter` | `modify_parameter: type=value \| payload_job=job_name[, type=value \|` | ENTYBEAN |  | [AS p.2571] |
| `no_change` | `• To specify a no_change value for CPU usage:` | OMCPU, OMD |  | [AS p.2586] |
| `one_way` | `one_way: TRUE \| FALSE` | WBSVC |  | [AS p.2597] |
| `port` | `port: port` | SNMPGET, SNMPSET | 161 | [AS p.2645] |
| `port_name` | `port_name: portname` | WBSVC, WSDOC |  | [AS p.2645] |
| `search_bw` | `search_btw: hours` | ZOSM |  | [AS p.2732] |
| `service_name` | `service_name: service` | WBSVC, WSDOC |  | [AS p.2736] |

## os-monitor (31)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `cpu_usage` | `cpu_usage: FREE \| USED` | OMCPU |  | [AS p.2454] |
| `disk_drive` | `disk_drive: drive` | OMD |  | [AS p.2462] |
| `disk_format` | `disk_format: PERCENT \| GB \| MB \| KB \| B` | OMD |  | [AS p.2463] |
| `disk_space` | `disk_space: FREE \| USED` | OMD |  | [AS p.2464] |
| `ip_host` | `ip_host: ip_address` | OMIP |  | [AS p.2527] |
| `ip_port` | `ip_port: ip_port` | OMIP |  | [AS p.2528] |
| `ip_status` | `ip_status: RUNNING \| STOPPED` | OMIP |  | [AS p.2529] |
| `lower_boundary` | `lower_boundary: start_range` | OMCPU, OMD, OMTF |  | [AS p.2552] |
| `monitor_cond` | `monitor_cond: condition` | DBMON |  | [AS p.2572] |
| `ping_ports` | `ping_ports: port \| port,port,...` | WOL |  | [AS p.2642] |
| `ping_timeout` | `ping_timeout: timeout` | WOL | 120 seconds | [AS p.2643] |
| `process_name` | `process_name: process_name` | OMP |  | [AS p.2648] |
| `process_status` | `process_status: RUNNING \| STOPPED` | OMP |  | [AS p.2650] |
| `text_file_filter` | `text_file_filter: textstring` | OMTF |  | [AS p.2782] |
| `text_file_filter_exists` | `text_file_filter_exists: TRUE \| FALSE` | OMTF |  | [AS p.2784] |
| `text_file_mode` | `text_file_mode: LINE \| REGEX \| DATETIME` | OMTF |  | [AS p.2785] |
| `text_file_name` | `text_file_name: file_name` | OMTF |  | [AS p.2787] |
| `time_format` | `time_format: time_format` | OMTF |  | [AS p.2788] |
| `time_position` | `time_position: timepos` | OMTF |  | [AS p.2790] |
| `upper_boundary` | `upper_boundary: end_range` | OMCPU, OMD, OMTF |  | [AS p.2797] |
| `win_event_category` | `win_event_category: event_category` | OMEL |  | [AS p.2825] |
| `win_event_computer` | `win_event_computer: computer_name` | OMEL |  | [AS p.2825] |
| `win_event_datetime` | `win_event_datetime: "yyyymmdd hh:mm:ss"` | OMEL |  | [AS p.2826] |
| `win_event_description` | `win_event_description: event_description` | OMEL |  | [AS p.2826] |
| `win_event_id` | `win_event_id: id` | OMEL |  | [AS p.2827] |
| `win_event_op` | `win_event_op: GT \| LT \| LE \| EQ \| GE` | OMEL |  | [AS p.2828] |
| `win_event_source` | `win_event_source: source_name` | OMEL |  | [AS p.2828] |
| `win_event_type` | `win_event_type: ERROR \| WARN \| INFO \| AUDITS \| AUDITF` | OMEL |  | [AS p.2829] |
| `win_log_name` | `win_log_name: log_name` | OMEL |  | [AS p.2830] |
| `win_service_name` | `win_service_name: service_name` | OMS |  | [AS p.2830] |
| `win_service_status` | `win_service_status: RUNNING \| STOPPED \| CONTINUE_PENDING \|` | OMS |  | [AS p.2831] |

## pam (6)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `form_parameter` | `name=value` |  |  | [AS p.2477] |
| `pa_monitor_progress` | `pa_monitor_progress: y \| n` | PAPROC, PAREQ |  | [AS p.2633] |
| `pa_name` | `pa_name: name` | PAPROC, PAREQ |  | [AS p.2634] |
| `pa_parameter` | `pa_parameter: param_name=name, param_value=value` | PAPROC, PAREQ |  | [AS p.2634] |
| `pa_path` | `pa_path: path` | PAREQ |  | [AS p.2635] |
| `pa_trace` | `pa_trace: y \| n` | PAPROC, PAREQ |  | [AS p.2636] |

## platform-microfocus (6)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `mf_jcl_name` | `mf_jcl_name: jcl_file` | MICROFOCUS |  | [AS p.2566] |
| `mf_jcl_type` | `mf_jcl_type: CONTENT \| REFERENCE` | MICROFOCUS |  | [AS p.2566] |
| `mf_server` | `mf_server: server_name \| "tcp:ip_address:port"` | MICROFOCUS |  | [AS p.2567] |
| `mf_server_address_type` | `mf_server_address_type: NAME \| ADDRESS` | MICROFOCUS |  | [AS p.2568] |
| `mf_user` | `mf_user: user_id@identifier` | MICROFOCUS |  | [AS p.2569] |
| `mf_version` | `mf_version: VSE/POWER \| JES2 \| JES3` | MICROFOCUS |  | [AS p.2569] |

## scheduling (10)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `date_conditions` | `date_conditions: y \| n` | ALL |  | [AS p.2455] |
| `days_of_week` | `` | ALL | No days are selected. | [AS p.2456] |
| `exclude_calendar` | `exclude_calendar: calendar_name` | ALL | No calendar is used. | [AS p.2471] |
| `must_complete_times` | `` | ALL |  | [AS p.2576] |
| `must_start_times` | `` | ALL |  | [AS p.2579] |
| `run_calendar` | `run_calendar: calendar_name` | ALL | No calendar is used. | [AS p.2690] |
| `run_window` | `run_window: "time-time"` | ALL | No run window is used. | [AS p.2691] |
| `start_mins` | `start_mins: mins [, mins]...` | ALL | No start time is set. | [AS p.2759] |
| `start_times` | `start_times: "time [, time]..."` | ALL |  | [AS p.2759] |
| `timezone` | `timezone: zone` | ALL |  | [AS p.2791] |

## security (4)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `os_user` | `os_user: os_userid@identifier` | MICROFOCUS |  | [AS p.2628] |
| `user_role` | `user_role: user_type` | DBMON, DBPROC, DBTRIG |  | [AS p.2802] |
| `wake_password` | `` | WOL |  | [AS p.2803] |
| `web_user` | `web_user: user_name` | WBSVC |  | [AS p.2824] |

## sla (12)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `box_failure` | `box_failure: conditions` | TODAY |  | [AS p.2421] |
| `box_success` | `box_success: conditions` |  |  | [AS p.2423] |
| `job_terminator` | `job_terminator: Y \| N` | BOX, CMD, DBMON, DBPROC, DBTRIG, FT, +26 more |  | [AS p.2548] |
| `max_exit_success` | `max_exit_success: exit_code` | CMD, I5, MICROFOCUS | 0 | [AS p.2560] |
| `max_run_alarm` | `max_run_alarm: mins` | ALL | No maximum set. | [AS p.2561] |
| `min_run_alarm` | `min_run_alarm: mins` | ALL | No minimum set. | [AS p.2570] |
| `n_retrys` | `n_retrys: attempts` | ALL | 0 | [AS p.2585] |
| `retry_on_failure_count` | `retry_on_failure_count: attempts` |  | 0 (no retries) | [AS p.2685] |
| `retry_on_failure_delay` | `retry_on_failure_delay: delay` |  | 10 | [AS p.2686] |
| `retry_on_failure_details` | `retry_on_failure_details: TRUE \| FALSE` |  | FALSE | [AS p.2686] |
| `success_codes` | `success_codes: exitcodes` | CMD, HTTP, I5, MICROFOCUS, PROXY, WSDOC | 0 | [AS p.2771] |
| `term_run_time` | `term_run_time: mins` | ALL | 0 (the job is allowed to run forever) | [AS p.2781] |

## web (70)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `connection_factory` | `connection_factory: factory` | JMSPUB, JMSSUB |  | [AS p.2446] |
| `connection_retry` | `connection_retry: number_of_retries` |  | 3 | [AS p.2447] |
| `connection_timeout` | `connection_timeout: time_in_seconds` |  | 0 | [AS p.2447] |
| `header_filter` | `header_filter: filter` |  |  | [AS p.2504] |
| `headers` | `headers: name1="value1", name2="value2"` |  |  | [AS p.2505] |
| `input_cookies` | `input_cookies: jobname` |  |  | [AS p.2524] |
| `invocation_type` | `invocation_type: GET \| POST \| PUT \| DELETE` |  |  | [AS p.2527] |
| `j2ee_authentication_order` | `` |  |  | [AS p.2529] |
| `j2ee_conn_domain` | `j2ee_conn_domain: origin_domain` |  |  | [AS p.2530] |
| `j2ee_conn_origin` | `j2ee_conn_origin: origin_host` |  | The computer name where the agent is running | [AS p.2531] |
| `j2ee_conn_user` | `j2ee_conn_user: authenticated_user@connhost` |  |  | [AS p.2532] |
| `j2ee_no_global_proxy_defaults` | `j2ee_no_global_proxy_defaults: Y \| N` |  |  | [AS p.2533] |
| `j2ee_parameter` | `j2ee_parameter: type=value \| payload_job=job_name[, type=value \|` | JAVARMI, JMSPUB, SESSBEAN |  | [AS p.2534] |
| `j2ee_proxy_domain` | `j2ee_proxy_domain: proxy_domain` |  |  | [AS p.2536] |
| `j2ee_proxy_host` | `j2ee_proxy_host: proxy_host` |  |  | [AS p.2536] |
| `j2ee_proxy_origin_host` | `j2ee_proxy_origin_host: proxy_origin` |  |  | [AS p.2537] |
| `j2ee_proxy_port` | `j2ee_proxy_port: proxy_port` |  |  | [AS p.2538] |
| `j2ee_proxy_user` | `j2ee_proxy_user: proxy_user` |  |  | [AS p.2539] |
| `j2ee_user` | `j2ee_user: user_name` | ENTYBEAN, JMSPUB, JMSSUB, SESSBEAN |  | [AS p.2540] |
| `jmx_parameter` | `jmx_parameter: type=value \| payload_job=job_name[, type=value \| payload_job=job_name...]` | JMXMAS, JMXMC, JMXMOP |  | [AS p.2543] |
| `jmx_user` | `jmx_user: user_name` | JMXMAG, JMXMAS, JMXMC, JMXMOP, JMXMREM, JMXSUB |  | [AS p.2545] |
| `mbean_attr` | `mbean_attr: attribute` | JMXMAG, JMXMAS |  | [AS p.2561] |
| `mbean_name` | `mbean_name: "domain_name:key=value[,key=value...]"` | JMXMAG, JMXMAS, JMXMC, JMXMOP, JMXMREM, JMXSUB |  | [AS p.2562] |
| `mbean_operation` | `mbean_operation: operation` | JMXMOP |  | [AS p.2563] |
| `message_class` | `message_class: class` | JMSPUB |  | [AS p.2564] |
| `operation_type` | `operation_type: CREATE \| UPDATE \| REMOVE` | ENTYBEAN |  | [AS p.2598] |
| `payload_uri` | `payload_uri: data` |  |  | [AS p.2637] |
| `persist_output_cookies` | `persist_output_cookies: true \| false` |  | false | [AS p.2640] |
| `persist_output_header` | `persist_output_header: true \| false` |  | false | [AS p.2640] |
| `persist_output_payload` | `persist_output_payload: true \| false` |  | false | [AS p.2641] |
| `preemptive_authentication` | `preemptive_authentication: false` |  | false | [AS p.2646] |
| `provider_url` | `provider_url: "location"` | ENTYBEAN, JMSPUB, JMSSUB, SESSBEAN | Examples: | [AS p.2653] |
| `reply_to` | `reply_to: replyname` | JMSPUB |  | [AS p.2679] |
| `request_id` | `request_id: request_id` | OACOPY |  | [AS p.2681] |
| `return_class_name` | `return_class_name: return_class` | WBSVC |  | [AS p.2687] |
| `return_namespace` | `return_namespace: return_namespace` | WBSVC |  | [AS p.2688] |
| `return_xml_name` | `return_xml_name: XML_type` | WBSVC |  | [AS p.2689] |
| `snmp_auth_protocol` | `snmp_auth_protocol: MD5 \| SHA` | SNMPGET, SNMPSET |  | [AS p.2738] |
| `snmp_comm_string` | `snmp_comm_string: community` | SNMPGET, SNMPSET | public | [AS p.2739] |
| `snmp_context_engine_id` | `snmp_context_engine_id: context_engine_id'` | SNMPGET, SNMPSET |  | [AS p.2739] |
| `snmp_context_name` | `snmp_context_name: context_name` | SNMPGET, SNMPSET |  | [AS p.2740] |
| `snmp_host` | `snmp_host: host` | SNMPGET, SNMPSET |  | [AS p.2741] |
| `snmp_mib` | `snmp_mib: file_name` | SNMPGET, SNMPSET |  | [AS p.2742] |
| `snmp_oid` | `snmp_oid: oid` | SNMPGET, SNMPSET |  | [AS p.2743] |
| `snmp_privacy` | `snmp_privacy: DES \| AES` | SNMPGET, SNMPSET |  | [AS p.2744] |
| `snmp_privacy_user` | `snmp_privacy_user: user_name` | SNMPGET, SNMPSET |  | [AS p.2745] |
| `snmp_subtree` | `snmp_subtree: y \| n` | SNMPGET |  | [AS p.2746] |
| `snmp_table_view` | `snmp_table_view: y \| n` | SNMPGET |  | [AS p.2746] |
| `snmp_value` | `snmp_value: type=value[, type=value...]` | SNMPSET |  | [AS p.2747] |
| `snmp_version` | `snmp_version: 1 \| 2 \| 3` | SNMPGET, SNMPSET |  | [AS p.2749] |
| `soap_action` | `soap_action: webmethod/soapaction` |  |  | [AS p.2750] |
| `soap_version` | `soap_version: 1.2` |  | 1.1 | [AS p.2750] |
| `target_namespace` | `target_namespace: target_namespace` | WBSVC |  | [AS p.2780] |
| `URL` | `URL: "url"` | JMXMAG, JMXMAS, JMXMC, JMXMOP, JMXMREM, JMXSUB |  | [AS p.2800] |
| `use_topic` | `use_topic: TRUE \| FALSE` | JMSPUB, JMSSUB |  | [AS p.2801] |
| `web_parameter` | `web_parameter: xsd\:type=value \| payload_job=job_name[, xsd\:type=value \|` | WBSVC |  | [AS p.2823] |
| `ws_authentication_order` | `` | WSDOC |  | [AS p.2833] |
| `ws_conn_domain` | `ws_conn_domain: origin_domain` | WSDOC |  | [AS p.2834] |
| `ws_conn_origin` | `ws_conn_origin: origin_host` | WSDOC | The computer name where the agent is runningLimits: Up to 12 | [AS p.2834] |
| `ws_conn_user` | `ws_conn_user: authenticated_user@connhost` | WBSVC, WSDOC |  | [AS p.2835] |
| `ws_global_proxy_defaults` | `ws_global_proxy_defaults: Y \| N` | WSDOC |  | [AS p.2836] |
| `ws_parameter` | `` | WSDOC |  | [AS p.2837] |
| `ws_proxy_domain` | `ws_proxy_domain: proxy_domain` | WSDOC |  | [AS p.2839] |
| `ws_proxy_host` | `ws_proxy_host: proxy_host` | WSDOC |  | [AS p.2840] |
| `ws_proxy_origin` | `ws_proxy_origin: proxy_origin` | WSDOC |  | [AS p.2841] |
| `ws_proxy_port` | `ws_proxy_port: proxy_port` | WSDOC |  | [AS p.2842] |
| `ws_proxy_user` | `ws_proxy_user: authenticated_user@proxydomain` | WSDOC |  | [AS p.2843] |
| `ws_security` | `` | WSDOC |  | [AS p.2844] |
| `wsdl_operation` | `wsdl_operation: operation` | WBSVC, WSDOC |  | [AS p.2846] |
| `WSDL_URL` | `WSDL_URL: wsdl_url` | WBSVC, WSDOC |  | [AS p.2847] |

## zos (14)

| Attribute | Syntax | Supported job types | Default | Page |
|---|---|---|---|---|
| `jcl_library` | `jcl_library: library` | ZOS |  | [AS p.2541] |
| `jcl_member` | `jcl_member: member` | ZOS |  | [AS p.2542] |
| `submit_modifier` | `submit_modifier: Option1=”value1”[,Option2=”value2”… , OptionN=”valueN”]` | PROXY |  | [AS p.2769] |
| `zos_dataset` | `zos_dataset: jcl_library` | ZOSDST |  | [AS p.2848] |
| `zos_dsn_renamed` | `zos_dsn_renamed: Y \| N` | ZOSDST |  | [AS p.2849] |
| `zos_dsn_updated` | `zos_dsn_updated: Y \| N` | ZOSDST |  | [AS p.2850] |
| `zos_explicit_dsn` | `zos_explicit_dsn: TRUE \| FALSE` | ZOSDST |  | [AS p.2851] |
| `zos_ftp_direction` | `zos_ftp_direction: RECEIVE \| SEND` | ZOSDST |  | [AS p.2851] |
| `zos_ftp_host` | `zos_ftp_host: host_name` | ZOSDST |  | [AS p.2852] |
| `zos_ftp_userid` | `zos_ftp_userid: user` | ZOSDST |  | [AS p.2853] |
| `zos_jobname` | `zos_jobname: name` | ZOSM |  | [AS p.2853] |
| `zos_trigger_by` | `zos_trigger_by: name` | ZOSDST |  | [AS p.2854] |
| `zos_trigger_on` | `zos_trigger_on: number` | ZOSDST |  | [AS p.2855] |
| `zos_trigger_type` | `` |  |  | [AS p.2855] |


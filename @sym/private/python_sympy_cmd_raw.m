function A = python_sympy_cmd_raw(cmd, varargin)
%PYTHON_SYMPY_CMD_RAW  Run SymPy command and return strings

  persistent fin fout pid

  sbtag='<output_block>';
  stag='<output_item>';
  etag='</output_item>';
  ebtag='</output_block>';

  % first thing is printf the cmd for newlines
  cmd = sprintf(cmd);

  %headers = sprintf('import sympy as sp\nimport pickle\n\n');
  headers = sprintf([ 'import sys\n' ...
                      'sys.ps1 = ""; sys.ps2 = ""\n' ...
                      'import sympy as sp\n' ...
                      'import dill as pickle\n' ...
                      '\n']);


  %% load all the inputs into python as pickles
  s = sprintf('ins = []\n\n');

  for i=1:length(varargin)
    x = varargin{i};
    if (isa(x,'sym'))
      s = sprintf('%s# Load %d: pickle\n', s, i);
      % need to be careful here: pickle might have escape codes
      s = sprintf('%sins.append(pickle.loads("""%s"""))\n\n', s, x.pickle);
    elseif (ischar(x))
      s = sprintf('%s# Load %d: string\n', s, i);
      s = sprintf('%sins.append("%s")\n\n', s, x);
    elseif (isnumeric(x) && isscalar(x))
      % TODO: should pass tye actual double, see comments elsewhere
      % for this same problem in other direction
      s = sprintf('%s# Load %d: double\n', s, i);
      s = sprintf('%sins.append(%.24g)\n\n', s, x);
    else
      i, x
      error('don''t know how to move that variable to python');
    end
  end

  %% the actual command
  s = sprintf('%s%s\n\n', s, cmd);
  s = sprintf('%sout = fcn(ins)\n\n', s);

  %debug
  %s = sprintf('%sprint out\n\n', s);

  %% output

  s = sprintf('%sprint ""\n', s);
  s = sprintf('%sprint "%s"\n', s, sbtag);
  s = sprintf('%sprint "%s"\n', s, stag);
  s = sprintf('%sprint "%s"\n', s, etag);
  s = sprintf('%sfor item in out:\n', s);
  s = sprintf('%s    print "%s"\n', s, stag);
  s = sprintf('%s    print str(item)\n', s);
  s = sprintf('%s    print "%s"\n', s, etag);
  s = sprintf('%s    print "%s"\n', s, stag);
  s = sprintf('%s    print pickle.dumps(item, 0)\n', s);
  s = sprintf('%s    print "%s"\n\n', s, etag);
  s = sprintf('%sprint "%s"\n', s, ebtag);


  if exist('popen2', 'builtin')
    if isempty(pid)
      disp('we have popen2: opening new pipe for two-way ipc')
      %[fin, fout, pid] = popen2 ('/bin/python','-i')
   %  [fin, fout, pid] = popen2 ('/bin/python','-i -c "x=1; print x"')
      [fin, fout, pid] = popen2 ('/home/cbm/mydebugpython.sh')
      fputs (fin, headers);
      fprintf (fin, 'print "hello"\n');
      fflush(fin);
      %sleep(2)
      %ab = fgets(fout)
      %disp(ab)
      %keyboard
      %disp('paused'); pause
      % todo print a block and read it to make sure we're live
    %else
      %disp('we have existing popen2 pipe')
      %fin, fout,pid
    end
    fputs (fin, s);
    fflush(fin);
    %disp('paused before read'); pause
    out = readblock(fout, sbtag, ebtag);

  else
    disp('no two-way ipc, using system()')

  %% use a temp file
  % todo must be a way to pass string to python -c w/o temp file
  fname = 'temp_sym_python_cmd.py';

  fd = fopen(fname, 'w');
  fprintf(fd, '# temporary autogenerated code\n\n');
  fprintf(fd, '%s\n', headers);
  fprintf(fd, '%s\n', s);
  fclose(fd);

  [status,out] = system(['python ' fname]);
  if status ~= 0
    status
    out
    error('failed');
  end
end

  %% extract the output
  % should be a nicer way to do all this with regexp!
  try
    s = strfind(out, stag);
    e = strfind(out, etag);
    % detect length of newline (1 on unix, 2 on windows?)
    lnl = e(1)-s(1)-length(stag);
    A = {};
    for i = 1:(length(s)-1)
      A{i} = out( (s(i+1)+length(stag)+lnl) : (e(i+1)-1-lnl) );
    end
  catch
    error('failed to extract output')
    status, out, s, e, A
  end

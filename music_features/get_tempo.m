function [tempo] = get_tempo(beats_v, plot_tempo)
% Get tempo
%  [tempo] = get_tempo(beats_v)
%  beats_v : vector of beats as time stamps (the last beat is the end of the piece)
%  tempo   : array; beat count (:,1), time (:,2), tempo (:,3)

if nargin < 2 % Plot by default
    plot_tempo = true;
end

% Compute Tempo
l          = length(beats_v);
tempo      = zeros(l-1,3);
tempo(:,1) = (1:l-1);                           % beat count starting from 1
tempo(:,2) = (beats_v(1:l-1)+beats_v(2:l))./2;  % time from midpoint between two beats
tempo(:,3) = 60./(beats_v(2:l)-beats_v(1:l-1)); % tempo

% Optional plot
if plot_tempo
    figure('Name','Tempo','NumberTitle','off');
    hold on
    plot(tempo(:,2),tempo(:,3),'k-');
    xlabel('midpoint between two beats');
    ylabel('Tempo (bpm)');
    xlim([min(tempo(:,2)), max(tempo(:,2))])
    grid('minor')
end

end